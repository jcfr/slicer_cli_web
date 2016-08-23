import parseGroup from './group';

/**
 * Parse a <parameters> tag into a "panel" object.
 */
function parsePanel(panel) {
    var $panel = $(panel);
    return {
        advanced: $panel.attr('advanced') === 'true',
        groups: _.map($panel.find('parameters > label'), parseGroup)
    };
}

export default parsePanel;
