window.addEventListener("load", function () {
    const container = document.querySelector("#captcha-container");
    CaptchaScript.renderCaptcha(container, async (voucher) => {
            await ChallengeScript.submitCaptcha(voucher);
            window.location.reload(true);
        }
    );
});


function r(i, n, a) {
    return void 0 === a && (a = {}), b(this, void 0, void 0, (function () {
        var r, o, s, c, l, u, g, I, d, M = this;
        return v(this, (function (y) {
            switch (y.label) {
                case 0:
                    return y.trys.push([0, 2, , 3]), String.prototype.replaceAll || (String.prototype.replaceAll = function (A, e) {
                        return "[object regexp]" === Object.prototype.toString.call(A).toLowerCase() ? this.replace(A, e) : this.replace(new RegExp(A, "g"), e)
                    }), (0, t.X1)(a.defaultLocale, a.disableLanguageAutoSelection), i.dir = (0, t.Mt)(), (r = (0, e.L3)()) ? ((o = document.createElement("style")).textContent = atob(w.split(",")[1]), document.head.appendChild(o), (s = document.createElement("LINK")).rel = "stylesheet", s.href = "https://static.".concat((h = r.match(/\.((captcha|jsapi)\.[^\/]+)\//)) && 2 == h.length ? h[1] : "captcha.awswaf.com", "/fonts/AmazonEmberLt/stylesheet.css"), document.head.appendChild(s), !0 !== a.dynamicWidth && (i.style.width = void 0 !== a.width ? "".concat(a.width, "px") : "320px", i.style.margin = "0 auto"), l = null, [4, O(r, n, c = function () {
                        return Math.max(Math.min(i.offsetWidth, 640), 180)
                    }, u = function (A) {
                        l = A
                    }, a)]) : (i.appendChild((0, e.az)("p", null, (0, t.fL)("captcha_init_failed"))), [2]);
                case 1:
                    return g = y.sent(), i.appendChild(g.root), (0, t.cT)((function () {
                        return b(M, void 0, void 0, (function () {
                            var o, s;
                            return v(this, (function (l) {
                                switch (l.label) {
                                    case 0:
                                        return l.trys.push([0, 2, , 3]), i.dir = (0, t.Mt)(), (0, e.cS)(i), [4, O(r, n, c, u, a)];
                                    case 1:
                                        return g = l.sent(), i.appendChild(g.root), [3, 3];
                                    case 2:
                                        return o = l.sent(), null === (s = a.onError) || void 0 === s || s.call(a, A.pS.InternalOrExisting(o)), [3, 3];
                                    case 3:
                                        return [2]
                                }
                            }))
                        }))
                    })), window.addEventListener("resize", (function () {
                        l && l()
                    })), I = function () {
                        ß
                        var A;
                        L || (((null === (A = window.localStorage) || void 0 === A ? void 0 : A.getItem("awswaf_captcha_solve_timestamp")) || null) === Q ? setTimeout(I, 100) : window.location.reload())
                    }, I(), [3, 3];
                case 2:
                    throw d = y.sent(), (0, e.FL)(d), d;
                case 3:
                    return [2]
            }
            var h
        }))
    }))
}

const f = document.querySelector('form').appendChild('<div class="twocaptcha-amazon_waf-helper<input type="hidden" name="amazon_waf_captcha_voucher"><input type="hidden" name="amazon_waf_existing_token"></div>"')