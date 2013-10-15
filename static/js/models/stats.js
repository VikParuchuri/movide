$(document).ready(function() {

    var ClassgroupStats = methodModel.extend({
        idAttribute: 'pk',
        url: function () {
            return '/api/classes/' + this.get('name') + "/stats/";
        }
    });

    var StatsView = BaseView.extend({
        el: "#stats-container",
        el_name: "#stats-container",
        chart_tag: "message-chart",
        network_chart_tag: "student-network-chart",
        events: {
        },
        initialize: function (options) {
            _.bindAll(this, 'render', 'create_daily_activity_chart', 'create_network_chart', 'render_charts');
            this.classgroup = options.classgroup;
            this.display_tag = options.display_tag;
            this.options = {
                classgroup: this.classgroup,
                display_tag: this.display_tag
            };
            this.render();
        },
        render: function(){
            var class_stats = new ClassgroupStats({name : this.classgroup});
            class_stats.fetch({success: this.render_charts, error: this.render_charts_error});
        },
        render_charts: function(model, success, options){
            var messages_by_day = [];
            var messages_by_day_data = model.get('message_count_by_day');
            for (var i = 0; i < messages_by_day_data.length; i++) {
                messages_by_day.push({created: messages_by_day_data[i].created_date, count: messages_by_day_data[i].created_count});
            }
            var network_info = model.get('network_info');
            if(messages_by_day.length > 1){
                this.create_daily_activity_chart(messages_by_day);
            } else {
                $("#" + this.chart_tag).html($('#noDailyActivityChartTemplate').html())
            }
            if(network_info.nodes.length > 2 && network_info.edges.length > 1){
                this.create_network_chart(network_info)
            } else {
                $("#" + this.network_chart_tag).html($('#noNetworkChartTemplate').html());
            }

        },
        create_daily_activity_chart: function(data){
            new Morris.Line({
                element: this.chart_tag,
                data: data,
                xkey: 'created',
                ykeys: ['count'],
                labels: ['# of messages']
            });
        },
        render_charts_error: function(){
            console.log("error");
        },
        create_network_chart: function(network_info){
            var sigInst = sigma.init(document.getElementById(this.network_chart_tag)).drawingProperties({
                defaultLabelColor: '#fff'
            }).graphProperties({
                    minNodeSize: 1,
                    maxNodeSize: 5,
                    minEdgeSize: 1,
                    maxEdgeSize: 5
                }).mouseProperties({
                    maxRatio: 4
                });

            var i;
            var clusters = [{
                'id': 1,
                'nodes': [],
                'color': 'rgb('+0+','+
                    0+','+
                    0+')'
            }];

            var cluster = clusters[0];
            var nodes = network_info.nodes;
            var edges = network_info.edges;
            var palette = colorbrewer.Paired[9];
            for(i=0;i<nodes.length;i++){
                var node = nodes[i];
                sigInst.addNode(node.name,{
                    'x': Math.random(),
                    'y': Math.random(),
                    'size': node.size,
                    'color': palette[(Math.random()*palette.length|0)],
                    'cluster': cluster['id'],
                    'label': node.name
                });
                cluster.nodes.push(node.name);
            }

            for(i = 0; i < edges.length; i++){
                var edge = edges[i];
                sigInst.addEdge(i,edge.start, edge.end, {'size' : 'strength'});
            }

            var greyColor = '#FFFFFF';
            sigInst.bind('overnodes',function(event){
                var nodes = event.content;
                var neighbors = {};
                sigInst.iterEdges(function(e){
                    if(nodes.indexOf(e.source)<0 && nodes.indexOf(e.target)<0){
                        if(!e.attr['grey']){
                            e.attr['true_color'] = e.color;
                            e.color = greyColor;
                            e.attr['grey'] = 1;
                        }
                    }else{
                        e.color = e.attr['grey'] ? e.attr['true_color'] : e.color;
                        e.attr['grey'] = 0;

                        neighbors[e.source] = 1;
                        neighbors[e.target] = 1;
                    }
                }).iterNodes(function(n){
                        if(!neighbors[n.id]){
                            if(!n.attr['grey']){
                                n.attr['true_color'] = n.color;
                                n.color = greyColor;
                                n.attr['grey'] = 1;
                            }
                        }else{
                            n.color = n.attr['grey'] ? n.attr['true_color'] : n.color;
                            n.attr['grey'] = 0;
                        }
                    }).draw(2,2,2);
            }).bind('outnodes',function(){
                    sigInst.iterEdges(function(e){
                        e.color = e.attr['grey'] ? e.attr['true_color'] : e.color;
                        e.attr['grey'] = 0;
                    }).iterNodes(function(n){
                            n.color = n.attr['grey'] ? n.attr['true_color'] : n.color;
                            n.attr['grey'] = 0;
                        }).draw(2,2,2);
                });

            sigInst.startForceAtlas2();
            setTimeout(function(){sigInst.stopForceAtlas2();}, 1500);
        }
    });

    window.StatsView = StatsView;
});