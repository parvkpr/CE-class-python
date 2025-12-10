classdef PhiGraph < handle
    properties
        nodes % changable

        maxima % changable

        val_longest_path
        seq_longest_path
    end

    methods
        function this = PhiGraph(ns)
            this.nodes = ns;
            this.val_longest_path = 0;
            this.seq_longest_path = [];
            this.set_imme();
            this.set_maxima();
            rng('default');
            rng(round(rem(now, 1)*1000000));
        end


        function set_imme(this)
            t_nodes = this.nodes;

            tsa = {};
            for nd = this.nodes
                tsa{end+1} = nd.smaller_all;
            end
            
            while true
                minima = [];
                min_idx = [];
                num = numel(t_nodes);
                
                for i = 1:num
                    if numel(t_nodes(i).smaller_all) == 1 %TODO: change to only legacy
                        minima = [minima t_nodes(i)];
                        min_idx = [min_idx i];
                    end
                end
                for mi = sort(min_idx, 'descend')
                    t_nodes(mi) = [];
                end

                for m = minima
                    for nn = t_nodes
                        if m.pn_is_member(nn.smaller_all)
                            % if m.greater_all has intersection with
                            % nn.smaller_all, then flag = true and nn is not
                            % greater_imme of m
                            flag = false;
                            for sn = nn.smaller_all
                                if ~sn.pn_is_equal(nn) && ~sn.pn_is_equal(m) && sn.pn_is_member(m.greater_all)
                                        flag = true;
                                        break;
                                end
                            end
                            if flag == false
                                nn.add_to_smaller_imme(m);
                                m.add_to_greater_imme(nn);
                            end
        
                            % remove m from nn.smaller_all
                            for i = 1:numel(nn.smaller_all)
                                if nn.smaller_all(i).pn_is_equal(m)
                                    nn.smaller_all(i) = [];
                                    break;
                                end
                            end
                        end
                    end
                end

                if numel(t_nodes) == 1
                    break;
                end
            end

            for nnd = 1: numel(this.nodes)
                this.nodes(nnd).smaller_all = tsa{nnd};
            end
        end

        function set_maxima(this)
            this.maxima = [];
            for n = this.nodes
                if numel(n.greater_imme) == 0
                    this.maxima = [this.maxima n];
                end
            end
        end

        function set_active_maxima(this)
            this.maxima = [];

            for n = this.nodes
                if n.active
                    great_exists = false;
                    for gi = n.greater_imme
                        if gi.active
                            great_exists = true;
                            break
                        end
                    end
                    if great_exists == false
                        this.maxima = [this.maxima n];
                    end
                end
            end

        end

        % obsolete
        function prune(this, brce)
            queue = this.maxima;
            while numel(queue) > 0
                head = queue(1);
                queue(1) = [];
                rob = brce.CheckSpec(head.phi);
                if rob < 0
                    for gn = head.greater_imme
                        gn.remove_from_smaller_imme(head);
                    end
                    for sn = head.smaller_imme
                        queue = [queue sn];
                        sn.remove_from_greater_imme(head);
                    end
                    this.remove_node(head);
                end
            end
            this.set_maxima();
        end
        %%%



        function remove_node(this, n)
            for i = 1: numel(this.nodes)
                if strcmp(this.nodes(i).get_phi_id(), n.get_phi_id())
                    this.nodes(i) = [];
                    break;
                end
            end
        end

        function e = empty(this)
            num = numel(this.maxima);
            e = (num == 0);
        end

        function e = symb_empty(this)
            e = true;
            for n = this.nodes
                if n.active == true
                    e = false;
                    break;
                end
            end
        end

        function nodes = covered(this, brce)
            nodes = [];
            for n = this.nodes
                rob = brce.CheckSpec(n.phi);
                if rob < 0
                    nodes = [nodes n];
                end
            end
        end

        function [path, val] = get_longest_path(this)
            this.val_longest_path = 0;
            this.seq_longest_path = [];

            if numel(this.maxima)~= 0
                for cur = this.maxima
                    this.dfs(cur, cur, 1);
                end
            end

            path = this.seq_longest_path;
            val = this.val_longest_path;
        end

        % aux function
        function dfs(this, seq, node, val)
            

            if node.active == true
                if val > this.val_longest_path
                    this.val_longest_path = val;
                    this.seq_longest_path = seq;
                end

                for s = node.smaller_imme
                    
                    this.dfs([seq s], s, val + 1);
                end
            end
        end

        function [path, val] = get_random_path(this)
            pool = this.maxima;
            path = [];
            
            while true
                num = 0;
                for m = pool
                    if m.active
                        num = num + 1;
                    end
                    
                end
                if num == 0
                    break;
                end
                selected = randi(num);
                selected_node = pool(selected);
                path = [path selected_node];
                val = numel(path);
                pool = selected_node.smaller_imme;
            end
        end

        function eliminate_hold(this, node, sys)
            if node.active ~= false
                node.active = false;
                node.add_to_results(sys);
                for g = node.greater_imme
                    this.eliminate_hold(g, sys);
                end
    
                this.set_active_maxima();
            end
        end

        function eliminate_unhold(this, node)
            if node.active ~= false
                node.active = false;
                for g = node.smaller_imme
                    this.eliminate_unhold(g);
                end
                %this.set_active_maxima();
            end
        end

        % from here on
        % code for visualization

        function visulize(this)
            s = [];
            t = [];
            names = {};
            d = dictionary;
            i = 1;
            for n = this.nodes
                d(get_id(n.phi)) = i;
                i = i + 1;
            end
            for n = this.nodes
                for sn = n.smaller_imme
                    s = [s d(get_id(n.phi))];
                    t = [t d(get_id(sn.phi))];
                end
                names{end + 1} = disp(n.phi);
            end
            weights = [];
            G = digraph(s,t,weights,names);
            p = plot(G,'Layout','layered');
            p.Marker = 'o';
            p.NodeColor = 'r';
            p.MarkerSize = 20;

        end

        function visulize_trace(this)
            s = [];
            t = [];
            names = {};
            d = dictionary;
            i = 1;
            for n = this.nodes
                d(get_id(n.phi)) = i;
                i = i + 1;
            end
            for n = this.nodes
                for sn = n.smaller_imme
                    s = [s d(get_id(n.phi))];
                    t = [t d(get_id(sn.phi))];
                end
                names{end + 1} = disp(n.phi);
            end
            weights = [];
            %names = {'A: alw[0,30](speed[t]<90 and RPM[t]<4000)', 'B', 'C', 'D','E', 'F: alw[0,t_1](speed[t]<90) and (alw[t_1,30](speed[t]<90)', 'G', 'H: alw[0,t_1](speed[t]<90)', 'I', 'J', 'K: alw[0,t_1](RPM[t]<4000) and (alw[t_1,30](RPM[t]<4000)', 'L', 'M', 'N: alw[t_1,30](speed[t]<90)', 'O', 'P: TRUE'};
            G = digraph(s,t,weights,names);
            %G = digraph(s,t);
            p = plot(G,'Layout','layered');
            p.Marker = 'o';
            p.NodeColor = 'b';
            p.MarkerSize = 20;
            for n = this.nodes
                if numel(n.results)~=0
                    highlight(p, d(get_id(n.phi)), 'NodeColor', 'r');
                end
            end
        end

        function visulize_active(this)
            s = [];
            t = [];
            names = {};
            d = dictionary;
            i = 1;
            for n = this.nodes
                d(get_id(n.phi)) = i;
                i = i + 1;
            end
            for n = this.nodes
                for sn = n.smaller_imme
                    s = [s d(get_id(n.phi))];
                    t = [t d(get_id(sn.phi))];
                end
                names{end + 1} = disp(n.phi);
            end
            weights = [];
            %names = {'A: alw[0,30](speed[t]<90 and RPM[t]<4000)', 'B', 'C', 'D','E', 'F: alw[0,t_1](speed[t]<90) and (alw[t_1,30](speed[t]<90)', 'G', 'H: alw[0,t_1](speed[t]<90)', 'I', 'J', 'K: alw[0,t_1](RPM[t]<4000) and (alw[t_1,30](RPM[t]<4000)', 'L', 'M', 'N: alw[t_1,30](speed[t]<90)', 'O', 'P: TRUE'};
            G = digraph(s,t,weights,names);
            %G = digraph(s,t);
            p = plot(G,'Layout','layered');
            p.Marker = 'o';
            p.NodeColor = 'b';
            p.MarkerSize = 20;
            for n = this.nodes
                if n.active
                    highlight(p, d(get_id(n.phi)), 'NodeColor', 'r');
                end
            end
        end

        function visulize_trace_names(this, nam)
            s = [];
            t = [];
            %names = {};
            d = dictionary;
            i = 1;
            for n = this.nodes
                d(get_id(n.phi)) = i;
                i = i + 1;
            end
            for n = this.nodes
                for sn = n.smaller_imme
                    s = [s d(get_id(n.phi))];
                    t = [t d(get_id(sn.phi))];
                end
                %names{end + 1} = disp(n.phi);
            end
            weights = [];
            names = nam;
            G = digraph(s,t,weights,names);
            %G = digraph(s,t);
            p = plot(G,'Layout','layered');
            p.Marker = 'o';
            p.NodeColor = 'b';
            p.MarkerSize = 20;
            for n = this.nodes
                if numel(n.results)~=0
                    highlight(p, d(get_id(n.phi)), 'NodeColor', 'r');
                end
            end
        end

    end

end