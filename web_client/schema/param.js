import convertValue from './convert';
import widgetType from './widget';
import parseDefault from './default';
import parseConstraints from './constraint';

/**
 * Parse a parameter spec.
 * @param {XML} param The parameter spec
 * @returns {object}
 */
function parseParam(param) {
    var $param = $(param);
    var type = widgetType(param);
    var values = {};
    var channel = $param.find('channel');

    if (channel.length) {
        channel = channel.text();
    } else {
        channel = 'input';
    }

    if ((type === 'file' || type === 'image') && channel === 'output') {
        type = 'new-file';
    }

    if (!type) {
        console.warn('Unhandled parameter type "' + param.tagName + '"'); // eslint-disable-line no-console
    }

    if (type === 'string-enumeration' || type === 'number-enumeration') {
        values = {
            values: _.map($param.find('element'), function (el) {
                return convertValue(type, $(el).text());
            })
        };
    }

    return _.extend(
        {
            type: type,
            slicerType: param.tagName,
            id: $param.find('name').text() || $param.find('longflag').text(),
            title: $param.find('label').text(),
            description: $param.find('description').text(),
            channel: channel
        },
        values,
        parseDefault(type, $param.find('default')),
        parseConstraints(type, $param.find('constraints').get(0))
    );
}

export default parseParam;
