$(document).ready(function() {

    var Grading = methodModel.extend({
        idAttribute: 'pk',
        url: function () {
            return class_api_link + 'grading_queue/';
        }
    });

    var Gradings = Backbone.Collection.extend({
        idAttribute: 'resource_id',
        model: Grading,
        url: class_api_link + 'grading_queue/'
    });

    var GradingView = BaseView.extend({
        tagName: "div",
        className: "gradings",
        template_name: "#gradingTemplate",
        events: {
        },
        initialize: function(){
            _.bindAll(this, 'render');
            this.model.bind('change', this.render);
            this.model.bind('remove', this.unrender);
        },
        get_model_json: function(){
            return this.model.toJSON();
        },
        render: function () {
            var tmpl = _.template($(this.template_name).html());
            var model_json = this.get_model_json();
            var model_html = tmpl(model_json);

            $(this.el).html(model_html);
            return this;
        },
        destroy: function() {
            this.model.trigger('destroy', this.model, this.model.collection, {});
        },
        remove_el: function(){
            $(this.el).remove();
        }
    });

    var GradingsView = BaseView.extend({
        el: "#grading-queue-container",
        template_name: "#gradingsTemplate",
        collection_class: Gradings,
        view_class: GradingView,
        events: {
        },
        initialize: function(options){
            _.bindAll(this, 'render', 'fetch', 'rebind_events', 'stop_ice', 'initialize_ice', 'submit_answer');
            this.classgroup = options.classgroup;
            this.collection = new this.collection_class();
            this.trackers = [];
            this.fetch();
        },
        fetch: function(){
            var that = this;
            this.collection.fetch({
                success: function(collection) {
                    that.render();
                }
            });
        },
        render: function () {
            var tmpl = _.template($(this.template_name).html());
            var grading_html = "";

            var that = this;
            _.each(this.collection.models, function (item) {
                grading_html = grading_html + $(that.renderGrading(item)).html();
            }, this);

            $(this.el).html(tmpl({
                gradings: grading_html
            }));
            this.rebind_events();
            return this;
        },
        initialize_ice: function(){
            var answers = $(".grading div.answer");
            var that = this;
            _.each(answers, function(item){
                var tracker = new ice.InlineChangeEditor({
                    element: item,
                    handleEvents: true,
                    currentUser: { id: 1, name: current_user },
                    plugins : ['IceAddTitlePlugin', 'IceSmartQuotesPlugin', 'IceEmdashPlugin', {
                        name : 'IceCopyPastePlugin',
                        settings : {
                            pasteType : 'formattedClean',
                            preserve : 'p,a[href],i,em,b,span'
                        }
                    }
                    ]
                });
                tracker.startTracking();
                that.trackers.push(tracker);
            });
        },
        initialize_redactor: function() {
            var grading_containers = $('.grading');
            _.each(grading_containers, function(item){
                var answer = $('.answer-input', item);
                var editor_options = JSON.parse($('.editor-options', item).html());
                $(answer).redactor(editor_options);
            });
        },
        stop_ice: function(){
            _.each(this.trackers, function(item){
                item.stopTracking();
            });
            this.trackers = [];
        },
        ice_undo: function(event){
            event.preventDefault();
            var key = 0;
            var container = $(event.target).closest('.grading-view-container');
            var changes = container.find('span.ins, span.del');
            _.each(changes, function(){
                var change_key = parseInt(this.data('cid'));
                if(change_key > key){
                    key = change_key;
                }
            });
            tracker.rejectChange('[data-cid="'+ key + '"]')
        },
        submit_answer: function(event){
            event.preventDefault();
            var form = $(event.target).closest('form');
            var score = form.find('.score').val();
            var feedback = form.find('.feedback').val();
            var annotated_answer = form.find('.answer').html();
            var resource_id = form.data('resource-id');
            var user_id = form.data('user-id');

            var grading = new Grading({
                score: score,
                feedback: feedback,
                annotated_answer: annotated_answer,
                resource_id: resource_id,
                user_id: user_id
            });
            var that = this;
            grading.save(null, {
                success: function(){
                    that.refresh();
                }
            });
            return false;
        },
        refresh: function(){
            this.fetch();
            this.render();
        },
        rebind_events: function(){
            this.stop_ice();
            this.initialize_ice();
            var submit_buttons = $('.grading .submit');
            submit_buttons.unbind();
            submit_buttons.click(this.submit_answer);
        },
        remove_el: function(){
            $(this.el).remove();
        },
        renderGrading: function(item){
            var gradingView = new this.view_class({
                model: item
            });
            return gradingView.render().el;
        }
    });

    window.GradingsView = GradingsView;
});
