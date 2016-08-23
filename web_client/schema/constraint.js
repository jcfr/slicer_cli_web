import convertValue from './convert';

/**
 * Parse a `contraints` tag.
 */
function parseConstraints(type, constraints) {
    var $c = $(constraints);
    var spec = {};
    var min = $c.find('minimum').text();
    var max = $c.find('maximum').text();
    var step = $c.find('step').text();
    if (min) {
        spec.min = convertValue(type, min);
    }
    if (max) {
        spec.max = convertValue(type, max);
    }
    if (step) {
        spec.step = convertValue(type, step);
    }
    return spec;
}

export default parseConstraints;
