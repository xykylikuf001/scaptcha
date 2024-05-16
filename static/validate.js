const form_div = document.querySelector("form")

const c = document.createElement('div')
c.classList = "twocaptcha-amazon_waf-helper"
const input1 = document.createElement("input");
input1.type = "hidden";
input1.name = "amazon_waf_captcha_voucher";
input1.value = arguments[0]
const input2 = document.createElement("input");
input2.type = "hidden";
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
awsWafIntegration.getToken = initialize;


awsWafIntegration.submitCaptcha = function () {
    if (hasCaptchaVoucher()) {
        challengeScript.submitCaptcha(document.querySelector('input[name=amazon_waf_captcha_voucher]').value);
    }
};


// Rest of the code related to obfuscated parts remains unchanged
