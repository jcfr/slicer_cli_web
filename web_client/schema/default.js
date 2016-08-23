import convertValue from './convert';

/**
 * Parse a `default` tag returning an empty object when no default is given.
 */
function parseDefault(type, value) {
    var output = {};
    if (value.length) {
        output = {value: convertValue(type, value.text())};
    }
    return output;
}

export default parseDefault;
