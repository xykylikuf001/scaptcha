// Function for decoding obfuscated strings
function decodeString(index, length) {
    const decodedStrings = getDecodedStrings();
    return decodeString = function (i, l) {
        i = i - 0xb9;
        return decodedStrings[i];
    }, decodeString(index, length);
}

// Immediately-invoked function expression (IIFE)
(function (fn, num) {
    const decodeStr = decodeString, array = fn();
    while (true) {
        try {
            const calcValue = parseInt(decodeStr(0xc8)) + parseInt(decodeStr(0xc6)) / 0x2 * (-parseInt(decodeStr(0xbc)) / 0x3) + parseInt(decodeStr(0xc2)) / 0x4 * (-parseInt(decodeStr(0xc5)) / 0x5) + -parseInt(decodeStr(0xc1)) / 0x6 + parseInt(decodeStr(0xbf)) / 0x7 + -parseInt(decodeStr(0xcc)) / 0x8 * (-parseInt(decodeStr(0xc3)) / 0x9) + parseInt(decodeStr(0xc4)) / 0xa;
            if (calcValue === num) break;
            else array.push(array.shift());
        } catch (err) {
            array.push(array.shift());
        }
    }
}(getDecodedArray, 0x5fd68), (() => {
    const decodeStr = decodeString;
    let storedValue, proxyObj;
    Object.defineProperty(window, decodeStr(0xbd), {
        'get': function () {
            return getCaptcha();
        }, 'set': function (value) {
            storedValue = value;
        }
    });
    let getCaptcha = function () {
        const getScript = function (identifier) {
            const querySelector = decodeStr, elements = document['querySelectorAll'](querySelector(0xca));
            for (let i = 0x0; i < elements[querySelector(0xb9)]; i++) {
                const attribute = elements[i][querySelector(0xba)](querySelector(0xcd));
                if (typeof attribute === querySelector(0xcb) && attribute['indexOf'](identifier) > 0x0) return attribute;
            }
            return null;
        }, registerCaptchaWidget = function (id, args) {
            const decodeStr = decodeString, attributes = args[0x1] ? args[0x1] : args;
            // Registering captcha widget
            registerCaptchaWidget({
                'captchaType': 'amazon_waf',
                'inputId': id,
                'widgetId': id,
                'pageurl': window[decodeStr(0xc0)][decodeStr(0xc9)],
                'sitekey': attributes[decodeStr(0xc7)],
                'iv': attributes['iv'],
                'context': attributes['context'],
                'challenge_script': getScript('/challenge.js'),
                'captcha_script': getScript(decodeStr(0xbe))
            });
        };
        return storedValue && (proxyObj = new Proxy(storedValue, {
            'get': function (obj, prop) {
                return new Proxy(obj[prop], {
                    'apply': (fn, thisArg, args) => {
                        const decodeStr = decodeString;
                        const result = Reflect['apply'](fn, thisArg, args);
                        // Render captcha and attach it to the DOM
                        return fn['name'] === 'renderCaptcha' && (!fn['id'] && (fn['id'] = 'captcha-container'), setTimeout(() => {
                            registerCaptchaWidget(fn['id'], window[decodeStr(0xbb)] || args[0x2]);
                        }, 0x64)), result;
                    }
                });
            }
        })), proxyObj;
    };
})());

// Function for decoding obfuscated array of strings
function getDecodedArray() {
    const strings = [
        '6780340CTuOGw',
        '2094355jybIuh',
        '106082aFsPCA',
        'key',
        '282638NKMlGt',
        'href',
        'script',
        'string',
        '112YvhZlI',
        'src',
        'length',
        'getAttribute',
        'gokuProps',
        '36sdROzW',
        'CaptchaScript',
        '/captcha.js',
        '2053646Pixqts',
        'location',
        '2909298yZohsR',
        '4qRvtKK',
        '436338dFHuux'
    ];
    getDecodedArray = function () {
        return strings;
    };
    return getDecodedArray();
}
