classdef MyFP < handle

    properties
        sys
        phi
        graph
        
        max_time
        solver

        obj_best
        nb_obj_eval
        time_spent

        num_total_nodes
        num_remained_nodes
    end

    methods
        function this = MyFP(s, p)
            this.sys = s;
            this.phi = p;

            parser = Parser(this.phi);
            this.graph = parser.phi_graph;
            this.num_total_nodes = numel(this.graph.nodes);
            this.num_remained_nodes = this.num_total_nodes;

            this.obj_best = intmax;
            this.nb_obj_eval = 0;
            this.time_spent = 0;
        end

        function solve(this)
            tStart = tic;
            while ~this.graph.empty()
                this.time_spent = toc(tStart);
                if this.time_spent > this.max_time
                    for n = this.graph.nodes
                        disp(['Uncovered Node: ', get_id(n.phi), ' ', disp(n.phi), newline]);
                    end
                    this.num_remained_nodes = numel(this.graph.nodes);
                    break;
                end
                phi_max = this.graph.get_maximum();
                falsif_pb = FalsificationProblem(this.sys, phi_max.phi);
                if this.max_time - this.time_spent >  this.max_time/5
                    falsif_pb.max_time = this.max_time/5;
                else
                    falsif_pb.max_time = this.max_time - this.time_spent;
                end
                falsif_pb.setup_solver(this.solver);
                falsif_pb.solver_options.Seed = round(rem(now,1)*1000000);
                falsif_pb.solve();
                
                if falsif_pb.obj_best < 0
                    
                    time = toc(tStart);
                    disp(['Time: ', num2str(time), newline]);
                    covered_nodes = this.graph.covered(falsif_pb.BrSys);
                    for cn = covered_nodes
                        disp(['Covered Node: ', get_id(cn.phi), ' ', disp(cn.phi), newline]);
                    end
                    this.graph.prune(falsif_pb.BrSys);
                end
                if falsif_pb.obj_best < this.obj_best
                    this.obj_best = falsif_pb.obj_best;
                end
                this.nb_obj_eval = this.nb_obj_eval + falsif_pb.nb_obj_eval;
            end
        end

        function setup_solver(this, solver)
            this.solver = solver;
        end



    end
end