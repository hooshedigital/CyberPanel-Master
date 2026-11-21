"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const script = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
const defaultConfig = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "public-config.json"), "utf8"));

async function render(config, lang = 'fa') {
  function element(key) {
    return {
      id: key, dataset: { product: key }, attrs: { "aria-disabled": "true" }, href: undefined,
      setAttribute(name, value) { this.attrs[name] = value; },
      removeAttribute(name) { delete this.attrs[name]; },
      getAttribute(name) { return this.attrs[name]; }
    };
  }
  const nodes = { "integration-state": { textContent: "preview" }, "client-login": element("login"), "domain-order": element("domain") };
  const productLinks = [element("hosting"), element("vps")];
  const document = {
    documentElement: { lang },
    getElementById(id) { return nodes[id]; },
    querySelectorAll(selector) { return selector === "[data-product]" ? productLinks : []; }
  };
  const fetch = () => Promise.resolve({ ok: true, json: () => Promise.resolve(config) });
  vm.runInNewContext(script, { document, URL, fetch });
  // Allow the promise chain (fetch -> json -> configure) to complete.
  await new Promise((resolve) => setImmediate(resolve));
  return { nodes, products: productLinks };
}

test("default public config has no ordering or login URLs", async () => {
  const { nodes, products } = await render(defaultConfig);
  assert.equal(nodes["client-login"].href, undefined);
  assert.equal(nodes["domain-order"].href, undefined);
  for (const product of products) assert.equal(product.href, undefined);
});

test("owned-domain HTTPS configuration creates exact WHMCS checkout links", async () => {
  const { nodes, products } = await render({
    schemaVersion: 1,
    billingBaseUrl: "https://billing.hooshedigital.ir/whmcs",
    products: { hosting: { pid: 17 }, vps: { pid: 44 } }
  });
  assert.equal(nodes["client-login"].href, "https://billing.hooshedigital.ir/whmcs/clientarea.php");
  assert.equal(nodes["domain-order"].href, "https://billing.hooshedigital.ir/whmcs/cart.php?a=add&domain=register");
  assert.equal(products[0].href, "https://billing.hooshedigital.ir/whmcs/cart.php?a=add&pid=17");
  assert.equal(products[1].href, "https://billing.hooshedigital.ir/whmcs/cart.php?a=add&pid=44");
});

test("deny external, HTTP and credential-bearing billing origins", async () => {
  for (const url of [
    "http://billing.hooshedigital.ir/",
    "https://billing.hooshedigital.ir.evil.example/",
    "https://hooshedigital.ir@evil.example/",
    "https://evil.example@billing.hooshedigital.ir/",
    "https://billing.hooshedigital.ir:8090/",
    "javascript:alert(1)",
    "https://billing.hooshedigital.ir/?token=x",
  ]) {
    const { nodes, products } = await render({ schemaVersion: 1, billingBaseUrl: url, products: { hosting: { pid: 1 } } });
    assert.equal(nodes["client-login"].href, undefined, url);
    assert.equal(nodes["domain-order"].href, undefined, url);
    assert.equal(products[0].href, undefined, url);
  }
});

test("reject invalid product ids; never build arbitrary checkout query", async () => {
  for (const pid of [null, 0, -1, "1&admin=true", "2", 2.1, 999999999999999999]) {
    const { products } = await render({
      schemaVersion: 1, billingBaseUrl: "https://billing.hooshedigital.ir/", products: { hosting: { pid } }
    });
    assert.equal(products[0].href, undefined, String(pid));
  }
});


test("language selection is a real top-right header feature in both site variants", () => {
  const root = path.join(__dirname, "..");
  const fa = fs.readFileSync(path.join(root, "index.html"), "utf8");
  const en = fs.readFileSync(path.join(root, "en.html"), "utf8");
  const css = fs.readFileSync(path.join(root, "styles.css"), "utf8");
  for (const [html, lang] of [[fa, "fa"], [en, "en"]]) {
    assert.match(html, new RegExp('<html lang="' + lang + '" dir="' + (lang === "fa" ? "rtl" : "ltr") + '"'));
    assert.match(html, /class="container site-utility" dir="rtl"/);
    assert.match(html, /class="locale-switch"/);
    assert.match(html, /href="\.\/index\.html" lang="fa"/);
    assert.match(html, /href="\.\/en\.html" lang="en"/);
    assert.match(html, /https:\/\/github\.com\/hooshedigital/);
    assert.match(html, /rel="noopener noreferrer"/);
    assert.ok(html.indexOf("site-utility") < html.indexOf("container nav-wrap"));
    for (const selector of ['id="services"', 'id="experience"', 'id="how-it-works"', 'id="faq"', 'id="client-login"', 'id="domain-order"']) {
      assert.ok(html.includes(selector), lang + " missing " + selector);
    }
    for (const product of ['data-product="hosting"', 'data-product="vps"']) {
      assert.ok(html.includes(product), lang + " missing " + product);
    }
  }
  assert.match(css, /\.site-utility/);
  assert.match(css, /\.locale-option/);
  assert.match(css, /prefers-reduced-motion/);
});

test("English WHMCS setup status is localized; no fake payment activation", async () => {
  const { nodes } = await render({
    schemaVersion: 1,
    billingBaseUrl: "https://billing.hooshedigital.ir/",
    products: { hosting: { pid: 7 } }
  }, "en");
  assert.match(nodes["integration-state"].textContent, /WHMCS order links are configured/);
  assert.match(nodes["integration-state"].textContent, /remain unverified/);
});
