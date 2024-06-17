const form_div = document.querySelector("form")
console.log(arguments)
const c = document.createElement('div')
c.classList = "twocaptcha-amazon_waf-helper"
const input1 = document.createElement("input");
input1.type = "text";
input1.name = "amazon_waf_captcha_voucher";
input1.value = arguments[0]
const input2 = document.createElement("input");
input2.type = "text";
input2.name = "amazon_waf_existing_token";
input2.value = arguments[1]

c.appendChild(input1)
c.appendChild(input2)
form_div.appendChild(c)


const challengeScript = window['ChallengeScript'];
const awsWafIntegration = window['AwsWafIntegration'];

function initialize() {
    const captchaVoucherInput = document.querySelector('input[name=amazon_waf_captcha_voucher]');
    const existingTokenInput = document.querySelector('input[name=amazon_waf_existing_token]');

    return {
        captcha_voucher: captchaVoucherInput ? captchaVoucherInput.value : undefined,
        existing_token: existingTokenInput ? existingTokenInput.value : undefined
    };
}

function hasCaptchaVoucher() {
    const captchaVoucherInput = document.querySelector('input[name=amazon_waf_captcha_voucher]');
    return !!(captchaVoucherInput && captchaVoucherInput.value);
}
AwsWafIntegration.hasToken = hasCaptchaVoucher;
AwsWafIntegration.getToken = initialize;


AwsWafIntegration.submitCaptcha = function () {
    if (hasCaptchaVoucher()) {
        ChallengeScript.submitCaptcha(document.querySelector('input[name=amazon_waf_captcha_voucher]').value);
    }
};

if (window.ChallengeScript !== undefined) {
    AwsWafIntegration.submitCaptcha();
}

// Rest of the code related to obfuscated parts remains unchanged
