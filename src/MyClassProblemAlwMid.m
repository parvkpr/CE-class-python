classdef MyClassProblemAlwMid < handle

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
        function this = MyClassProblemAlwMid(s, p, k)
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
            
            this.timeClass = 0;

            this.numclass = numel(this.graph.nodes);
        end

        function solve(this)

            tClass = tic;
            while ~this.graph.symb_empty()
                path = this.graph.get_longest_path();
    
                
                %for cur_ = path
                mid = ceil(numel(path)/2);
                cur = path(mid);
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
                    scopy = this.sys.copy();
                    cur.add_to_results(scopy);
                    this.graph.eliminate_hold(cur, scopy);
                else
                    this.graph.eliminate_unhold(cur);
                end

                %end
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