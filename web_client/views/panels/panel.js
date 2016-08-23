import View from 'girder/views/View';

import PanelTemplate from '../../templates/panel.jade';

import '../../stylesheets/panel/panel.styl';

var Panel = View.extend({
    events: {
        'show.bs.collapse': 'expand',
        'hide.bs.collapse': 'collapse',
        'click .h-panel-title-container': '_handleTitleClick'
    },
    initialize: function (settings) {
        this.spec = settings.spec;
    },
    render: function () {
        this.$el.html(PanelTemplate(this.spec));
    },
    expand: function () {
        this.$('.icon-down-open').attr('class', 'icon-up-open');
    },
    collapse: function () {
        this.$('.icon-up-open').attr('class', 'icon-down-open');
    },
    _handleTitleClick: function (e) {
        if (!$(e.target).hasClass('h-remove-panel')) {
            e.stopPropagation();
            this.$('.h-panel-content').collapse('toggle');
        }
    }
});

export default Panel;
