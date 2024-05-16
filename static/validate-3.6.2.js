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
