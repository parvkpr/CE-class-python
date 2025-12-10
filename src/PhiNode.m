classdef PhiNode < handle
    properties
        phi
        
        greater_all
        smaller_all

        greater_imme % changable
        smaller_imme % changable

        active
        results % sys.copy()
    end

    methods
        function this = PhiNode(phi)
            this.phi = phi;
            this.greater_all = [];
            this.smaller_all = [];
            this.greater_imme = [];
            this.smaller_all = [];
            this.active = true;
            this.results = [];
        end

        function id = get_phi_id(this)
            id = get_id(this.phi);
        end

        function add_to_greater_all(this, g)
            exist_flag = false;
            for n = this.greater_all
                if strcmp(get_id(n.phi), get_id(g.phi))
                    exist_flag = true;
                    break;
                end
            end
            if ~exist_flag
                this.greater_all = [this.greater_all g];
            end
        end

        function add_to_smaller_all(this, s)
            exist_flag = false;
            for n = this.smaller_all
                if strcmp(get_id(n.phi), get_id(s.phi))
                    exist_flag = true;
                    break;
                end
            end
            if ~exist_flag
                this.smaller_all = [this.smaller_all s];
            end
        end

        function add_to_greater_imme(this, g)
            this.greater_imme = [this.greater_imme g];
        end

        function add_to_smaller_imme(this, s)
            this.smaller_imme = [this.smaller_imme s];
        end

        function remove_from_greater_imme(this, g)
            for i = 1:numel(this.greater_imme)
                if strcmp(g.get_phi_id(), this.greater_imme(i).get_phi_id())
                    this.greater_imme(i) = [];
                    break;
                end
            end
        end

        function remove_from_smaller_imme(this, s)
            for i = 1:numel(this.smaller_imme)
                if strcmp(s.get_phi_id(), this.smaller_imme(i).get_phi_id())
                    this.smaller_imme(i) = [];
                    break;
                end
            end
        end

        function pos = pn_is_member(this, nodes)
            pos = false;
            for n = nodes
                if this.pn_is_equal(n)
                    pos = true;
                    break;
                end
            end
        end

        function pos = pn_is_equal(this, node)
            pos = strcmp(get_id(this.phi), get_id(node.phi));
        end

        function add_to_results(this, sys)
            this.results = [this.results sys];
        end

    end
end