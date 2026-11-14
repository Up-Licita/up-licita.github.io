// busca.js — busca no navegador sobre dados/<uf>.json (gerados todo dia pelo robô).
// Cada linha: [url, objeto, cidade, segmento, valor, encerramento]
(function () {
  "use strict";
  var LIMITE = 300;
  var form = document.getElementById("form-busca");
  var status = document.getElementById("status");
  var lista = document.getElementById("resultados");
  var meta = null;
  var cache = {};

  function norm(t) {
    return (t || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }
  function esc(t) {
    return String(t == null ? "" : t).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function moeda(v) {
    if (typeof v !== "number" || v <= 0) return "";
    return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  }
  function prazo(iso) {
    if (!iso) return ["Prazo não informado", "normal"];
    var fim = new Date(iso), agora = new Date();
    var ms = fim - agora, dias = Math.floor(ms / 864e5);
    if (ms < 0) return ["Encerrada", "normal"];
    if (ms < 864e5) return ["Encerra em " + Math.max(1, Math.floor(ms / 36e5)) + " h", "urgente"];
    if (dias === 1) return ["Encerra amanhã", "urgente"];
    if (dias <= 5) return ["Encerra em " + dias + " dias", "breve"];
    return ["Encerra em " + fim.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }), "normal"];
  }

  function carregar(uf) {
    if (cache[uf]) return Promise.resolve(cache[uf]);
    return fetch("dados/" + uf.toLowerCase() + ".json")
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) { d.forEach(function (x) { x.push(uf); x.push(norm(x[1] + " " + x[2])); }); cache[uf] = d; return d; })
      .catch(function () { return []; });
  }

  function linha(x) {
    var p = prazo(x[5]), v = moeda(x[4]);
    return '<li class="lin"><a href="' + esc(x[0]) + '">' +
      '<span class="lin-prazo prazo-' + p[1] + '">' + esc(p[0]) + "</span>" +
      '<span class="lin-objeto">' + esc(x[1]) + "</span>" +
      '<span class="lin-meta"><span>' + esc(x[2]) + ", " + esc(x[6]) + "</span><span>" +
      esc((meta.segmentos || {})[x[3]] || "") + "</span>" +
      (v ? '<span class="lin-valor">' + esc(v) + "</span>" : "") + "</span></a></li>";
  }

  function buscar() {
    var q = norm(document.getElementById("q").value.trim());
    var uf = document.getElementById("uf").value;
    var seg = document.getElementById("seg").value;
    var params = new URLSearchParams();
    if (q) params.set("q", document.getElementById("q").value.trim());
    if (uf) params.set("uf", uf);
    if (seg) params.set("seg", seg);
    history.replaceState(null, "", "?" + params.toString());

    if (!uf && !q && !seg) {
      lista.innerHTML = "";
      status.textContent = "Digite o que você vende ou escolha um estado para ver as licitações.";
      return;
    }
    var ufs = uf ? [uf] : Object.keys(meta.ufs || {});
    status.textContent = uf ? "Buscando…" : "Buscando em todos os estados, pode levar alguns segundos…";
    Promise.all(ufs.map(carregar)).then(function (partes) {
      var termos = q ? q.split(/\s+/) : [];
      var res = [];
      partes.forEach(function (d) {
        d.forEach(function (x) {
          if (seg && x[3] !== seg) return;
          for (var i = 0; i < termos.length; i++) if (x[7].indexOf(termos[i]) === -1) return;
          res.push(x);
        });
      });
      res.sort(function (a, b) { return (a[5] || "9") < (b[5] || "9") ? -1 : 1; });
      if (!res.length) {
        lista.innerHTML = "";
        status.textContent = "Nenhuma licitação aberta com esses filtros. Tente uma palavra mais curta (ex.: \"cimento\" em vez de \"cimento CP-II 50kg\") ou outro estado.";
        return;
      }
      var total = res.length.toLocaleString("pt-BR");
      status.textContent = res.length > LIMITE
        ? total + " licitações encontradas. Mostrando as " + LIMITE + " que encerram primeiro."
        : total + (res.length === 1 ? " licitação encontrada." : " licitações encontradas.");
      lista.innerHTML = res.slice(0, LIMITE).map(linha).join("");
    });
  }

  fetch("dados/meta.json").then(function (r) { return r.json(); }).then(function (m) {
    meta = m;
    var p = new URLSearchParams(location.search);
    document.getElementById("q").value = p.get("q") || "";
    document.getElementById("uf").value = p.get("uf") || "";
    document.getElementById("seg").value = p.get("seg") || "";
    buscar();
  }).catch(function () {
    status.textContent = "Não foi possível carregar as licitações agora. Atualize a página em instantes.";
  });

  form.addEventListener("submit", function (ev) { ev.preventDefault(); buscar(); });
})();
