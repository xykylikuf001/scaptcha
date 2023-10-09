const form_div = document.querySelector("form")

// const c = document.createElement('div')
// c.classList = "twocaptcha-amazon_waf-helper"
const input1 = document.createElement("input");
input1.type = "hidden";
input1.name = "amazon_waf_captcha_voucher";
input1.value = arguments[0]
const input2 = document.createElement("input");
input2.type = "hidden";
input2.name = "amazon_waf_existing_token";
input2.value = arguments[1]

form_div.appendChild(input1)
form_div.appendChild(input2)


AwsWafIntegration.getToken = function () {
    return {
        captcha_voucher: document.querySelector("input[name=amazon_waf_captcha_voucher]").value,
        existing_token: document.querySelector("input[name=amazon_waf_existing_token]").value
    }
}

AwsWafIntegration.hasToken = function () {
    const captcha_voucher_input = document.querySelector("input[name=amazon_waf_captcha_voucher]");
    return !!(captcha_voucher_input && captcha_voucher_input.value);
}

if (window.ChallengeScript !== undefined) {
    ChallengeScript.submitCaptcha(document.querySelector("input[name=amazon_waf_captcha_voucher]").value);
}