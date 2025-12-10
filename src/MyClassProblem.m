classdef MyClassProblem < handle

    properties
        sys
        phi
        k

        graph
        
        max_time
        solver

        

        interval_dict

        %results
        numclass
        %numcovered
        totaltime
        timeSplit
        timeClass

    end

    methods
        function this = MyClassProblem(s, p, k)
            this.sys = s;
            this.phi = p;
            this.k = k;

            this.totaltime = 0;
            this.timeSplit = 0;

            tSplit = tic;
            parser = Parser(this.phi, k);
            this.totaltime = this.totaltime + toc(tSplit);
            this.timeSplit = toc(tSplit);

            this.graph = parser.phi_graph;
            this.interval_dict = parser.interval_dict;
%             this.num_total_nodes = numel(this.graph.nodes);
%             this.num_remained_nodes = this.num_total_nodes;
% 
%             this.obj_best = intmax;
%             this.nb_obj_eval = 0;
            
            

            this.timeClass = 0;

            this.numclass = numel(this.graph.nodes);
            %this.numcovered = 0;
        end

        function solve(this)
            queue = {};
            for pm = this.graph.maxima
                queue{end+1} = pm;
            end

            %while ~this.graph.symb_empty()
            tClass = tic;
            while numel(queue)~=0
                cur = queue{1};
                queue(1) = [];
                if cur.active == false
                    continue
                end
                vars = fieldnames(get_params(cur.phi))';
                ranges = [];
                keycell = keys(this.interval_dict, 'cell');
                for iv = 1:numel(vars)
                    rg = [];
                    for ik = 1:numel(keycell)
                        if startsWith(vars{iv}, keycell{ik})
                            rg = this.interval_dict(keycell{ik});
                            break;
                        end
                    end
                    ranges = [ranges; eval(rg)];
                end
                spec = phi_merge(cur.phi, 'not', 'target');

                if numel(vars) == 0
                    res = - this.sys.CheckSpec(spec);
                else
                    synth_pb = MyParamSynthProblem(this.sys, spec, vars, ranges);
                    synth_pb.setup_solver('cmaes');
                    synth_pb.max_time = this.max_time;
                    synth_pb.solve();
                    res = synth_pb.obj_best;
                end


                if res < 0
                    cur.add_to_results(this.sys.copy());
                    for nd = cur.smaller_imme
                        if nd.active
                            %check membership of nd in queue
                            isThere = false;
                            for iq = 1: numel(queue)
                                if strcmp(queue{iq}.get_phi_id(), nd.get_phi_id())
                                    isThere = true;
                                    break;
                                end
                            end
                            %check end
                            if isThere == false
                                queue{end+1} = nd;
                            end
                        end
                    end
                else
                    for nd = cur.smaller_all
                        nd.active = false;
                    end
                end
            end
            
            this.timeClass = toc(tClass);
            this.totaltime = this.totaltime + this.timeClass;

            disp('END');
        end

        function setup_sys(this, sys)
            this.sys = sys;
        end

        function setup_solver(this, solver)
            this.solver = solver;
        end



    end
end