import parseParam from './param';

/**
 * Parse a parameter group (deliminated by <label> tags) within a
 * panel.
 */
function parseGroup(label) {
    // parameter groups inside panels
    var $label = $(label),
        $description = $label.next('description');

    return {
        label: $label.text(),
        description: $description.text(),
        parameters: _.map($description.nextUntil('label'), parseParam)
    };
}

export default parseGroup;
