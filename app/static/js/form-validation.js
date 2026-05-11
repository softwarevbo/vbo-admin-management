/**
 * Client-side guards: required (mirrors admin rules via data-rule-required),
 * disable double-submit + spinner, optional AJAX duplicate check (data-rule-unique).
 */
(function () {
  function csrfToken() {
    var m = document.querySelector('meta[name="csrf-token"]');
    return m ? m.getAttribute("content") : "";
  }

  function guardForm(form) {
    if (!form.hasAttribute("data-guard-submit")) return;

    form.addEventListener(
      "submit",
      function (e) {
        var ok = true;
        form.querySelectorAll("[data-rule-required]").forEach(function (el) {
          if (el.type === "file") {
            if (
              el.hasAttribute("data-rule-required") &&
              el.getAttribute("data-rule-required") === "1" &&
              (!el.files || !el.files.length)
            ) {
              el.classList.add("is-invalid");
              ok = false;
            } else el.classList.remove("is-invalid");
            return;
          }
          if (el.type === "checkbox") return;
          var req = el.getAttribute("data-rule-required") === "1";
          var v = el.value != null ? String(el.value).trim() : "";
          if (req && !v) {
            el.classList.add("is-invalid");
            ok = false;
          } else {
            el.classList.remove("is-invalid");
          }
        });
        if (!ok) {
          e.preventDefault();
          e.stopPropagation();
          form.classList.add("was-validated");
          return false;
        }
        form
          .querySelectorAll("[data-guard-submit-btn], [type=submit]")
          .forEach(function (btn) {
            btn.disabled = true;
          });
        form.querySelectorAll("[data-submit-spinner]").forEach(function (sp) {
          sp.classList.remove("d-none");
        });
      },
      true
    );
  }

  function bindRemoteChecks() {
    var debounceTimers = {};
    document.querySelectorAll("[data-rule-unique='1']").forEach(function (el) {
      var ev = el.tagName === "SELECT" ? "change" : "blur";
      el.addEventListener(ev, function () {
        var fname = el.name;
        if (!fname) return;
        var form = el.closest("form");
        if (!form || form.getAttribute("data-validate-module") == null) return;
        var mod = form.getAttribute("data-validate-module");
        var ex = form.getAttribute("data-validate-exclude-id");
        var billId = form.getAttribute("data-bill-id");
        var vid = form.querySelector("[name=vendor_id]");
        var vendorId = vid ? vid.value : null;
        clearTimeout(debounceTimers[fname]);
        debounceTimers[fname] = setTimeout(function () {
          var params = new URLSearchParams({
            module: mod,
            field: el.name || field,
            value: el.value || "",
          });
          if (ex) params.set("exclude_id", ex);
          if (billId) params.set("exclude_bill_id", billId);
          if ((el.name === "vendor_bill_no") && vendorId) params.set("vendor_id", vendorId);
          fetch("/api/validate-field?" + params.toString(), { credentials: "same-origin" })
            .then(function (r) {
              return r.json();
            })
            .then(function (data) {
              if (!data.valid && data.message) {
                el.classList.add("is-invalid");
                var fb = el.parentElement.querySelector(".ajax-invalid-feedback");
                if (!fb) {
                  fb = document.createElement("div");
                  fb.className = "invalid-feedback d-block ajax-invalid-feedback";
                  el.parentElement.appendChild(fb);
                }
                fb.textContent = data.message;
              } else {
                el.classList.remove("is-invalid");
                var old = el.parentElement.querySelector(".ajax-invalid-feedback");
                if (old) old.remove();
              }
            })
            .catch(function () {});
        }, 450);
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("form").forEach(guardForm);
    bindRemoteChecks();
  });
})();
