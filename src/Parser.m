%and L, R, A(and), O(or)
classdef Parser < handle

    properties
        phi
        k %cell arrays, with hierarchy {1, {3,{3}},{5}}
        phi_graph

        %phi_dict % id ==> suff condition
        interval_dict % variable start with ==> interval
        simplify_dict % id of original nodes ==> id of nodes after simplification
        formula_dict % simplified id ==> formula
        simp_phi_dict 
    end

    methods
        function this = Parser(phi, k)
            this.phi = phi;
            this.k = k;
            %this.phi_dict = dictionary;
            this.simp_phi_dict = dictionary;
            this.interval_dict = dictionary;
            this.simplify_dict = dictionary;
            this.formula_dict = dictionary;
            this.parse_nodes();
        end

        function parse_nodes(this)
            %*** for debugging
            %this.parse_nodes_pos(this.phi, this.k);
            %***

            phis = this.parse_nodes_neg(this.phi, this.k);
%             for p = phis
%                 id = p.get_phi_id();
%                 this.phi_dict(id) = p;
%             end

            simp_phis = [];
            for p = phis
                id = p.get_phi_id();
                simp_id = this.simplify_dict(id);
                
                in_simp_phis = false;
                for sp = simp_phis
                    if strcmp(sp.get_phi_id(), simp_id)
                        in_simp_phis = true;
                        break;
                    end
                end
                if ~in_simp_phis
                    formula = this.formula_dict(simp_id);
                    simp_phis = [simp_phis PhiNode(formula)];
                end
            end

            for sp_ = simp_phis
                simp_id = sp_.get_phi_id();
                this.simp_phi_dict(simp_id) = sp_;
            end

            rels = this.parse_edges_neg(this.phi, this.k);
%             for r = rels
%                 gn = this.phi_dict(this.simplify_dict(r.greater));
%                 sn = this.phi_dict(this.simplify_dict(r.smaller));
%                 gn.add_to_smaller_all(sn);
%                 sn.add_to_greater_all(gn);
%             end
            for r = rels
                gn = this.simp_phi_dict(this.simplify_dict(r.greater));
                sn = this.simp_phi_dict(this.simplify_dict(r.smaller));
                gn.add_to_smaller_all(sn);
                sn.add_to_greater_all(gn);
            end
            
            this.phi_graph = PhiGraph(simp_phis);
        end

        function phis = parse_nodes_pos(this, phi, k)
            if strcmp(get_type(phi), 'predicate')
                phis = PhiNode(phi);
                this.simplify_dict(get_id(phi)) =  get_id(phi);
                this.formula_dict(get_id(phi)) = phi;

                %sig = STL_ExtractSignals(phi);
                f_stl = STL_Formula('FALSE', 'false');     
                phis = [phis PhiNode(f_stl)];
                this.simplify_dict('FALSE') = 'FALSE';
                this.formula_dict('FALSE') = f_stl;
                
            elseif strcmp(get_type(phi), 'not')
                phis = [];
                phis_ = this.parse_nodes_neg(get_phis(phi, 0), k{2});

                for p = phis_
                    p_ = p.phi;
                    id_ = strcat('PosNot_', get_id(p_));
                    phi_ = phi_merge(p_, 'not', id_);
                    phis = [phis PhiNode(phi_)];
                    
                    p_simp_id = this.simplify_dict(get_id(p_));
                    if strcmp(p_simp_id, 'FALSE')
                        simplified_id = 'TRUE';
                        simp_phi_ = STL_Formula('TRUE', 'true');
                    elseif strcmp(p_simp_id, 'TRUE')
                        simplified_id = 'FALSE';
                        simp_phi_ = STL_Formula('FALSE', 'false');
                    else
                        simplified_id = strcat('PosNot_', p_simp_id);
                        simp_phi_ = phi_merge(this.formula_dict(p_simp_id), 'not', simplified_id);
                    end
                    this.simplify_dict(id_) = simplified_id;
                    this.formula_dict(simplified_id) = simp_phi_;

                end

            elseif strcmp(get_type(phi), 'and')
                phis = [];
                phis1 = this.parse_nodes_pos(get_phis(phi, 1), k{2});
                phis2 = this.parse_nodes_pos(get_phis(phi, 2), k{3});
                for p1 = phis1
                    for p2 = phis2
                        p1_ = p1.phi;
                        p2_ = p2.phi;

                        id_ = strcat('PosAnd_', get_id(p1_), get_id(p2_));
                        phi_ = phi_merge([p1_, p2_], 'and', id_);
                        phis = [phis PhiNode(phi_)];

                        p1_simp_id = this.simplify_dict(get_id(p1_));
                        p2_simp_id = this.simplify_dict(get_id(p2_));
                        if strcmp(p1_simp_id, 'FALSE') || strcmp(p2_simp_id, 'FALSE') 
                            simplified_id = 'FALSE';
                            simp_phi_ = STL_Formula('FALSE', 'false');
                        elseif strcmp(p1_simp_id, 'TRUE') && strcmp(p2_simp_id, 'TRUE')
                            simplified_id = 'TRUE';
                            simp_phi_ = STL_Formula('TRUE', 'true');
                        elseif strcmp(p1_simp_id, 'TRUE')
                            simplified_id = p2_simp_id;
                            simp_phi_ = this.formula_dict(p2_simp_id);
                        elseif strcmp(p2_simp_id, 'TRUE')
                            simplified_id = p1_simp_id;
                            simp_phi_ = this.formula_dict(p1_simp_id);
                        else
                            simplified_id = strcat('PosAnd_', p1_simp_id, p2_simp_id);
                            simp_phi_ = phi_merge([this.formula_dict(p1_simp_id), this.formula_dict(p2_simp_id)], 'and', simplified_id);
                        end
                        this.simplify_dict(id_) = simplified_id;
                        this.formula_dict(simplified_id) = simp_phi_;
                        
                    end
                end

            elseif strcmp(get_type(phi), 'or')
                phis = [];
                phis1 = this.parse_nodes_pos(get_phis(phi, 1), k{2});
                phis2 = this.parse_nodes_pos(get_phis(phi, 2), k{3});

                for p1 = phis1
                    for p2 = phis2
                        p1_ = p1.phi;
                        p2_ = p2.phi;
                        
                        id_ = strcat('PosOr_', get_id(p1_), get_id(p2_));
                        phi_ = phi_merge([p1_ p2_], 'or', id_);
                        phis = [phis PhiNode(phi_)];

                        p1_simp_id = this.simplify_dict(get_id(p1_));
                        p2_simp_id = this.simplify_dict(get_id(p2_));
                        if strcmp(p1_simp_id, 'TRUE') || strcmp(p2_simp_id, 'TRUE') 
                            simplified_id = 'TRUE';
                            simp_phi_ = STL_Formula('TRUE', 'true');
                        elseif strcmp(p1_simp_id, 'FALSE') && strcmp(p2_simp_id, 'FALSE')
                            simplified_id = 'FALSE';
                            simp_phi_ = STL_Formula('FALSE', 'false');
                        elseif strcmp(p1_simp_id, 'FALSE')
                            simplified_id = p2_simp_id;
                            simp_phi_ = this.formula_dict(p2_simp_id);
                        elseif strcmp(p2_simp_id, 'FALSE')
                            simplified_id = p1_simp_id;
                            simp_phi_ = this.formula_dict(p1_simp_id);
                        else
                            simplified_id = strcat('PosOr_', p1_simp_id, p2_simp_id);
                            simp_phi_ = phi_merge([this.formula_dict(p1_simp_id), this.formula_dict(p2_simp_id)], 'or', simplified_id);
                        end
                        this.simplify_dict(id_) = simplified_id;
                        this.formula_dict(simplified_id) = simp_phi_;
                    end
                end

            elseif strcmp(get_type(phi), 'always')
                phi_id = get_id(phi);
                phis = [];

                kNum = k{1};
                phis_ = this.parse_nodes_pos(get_phis(phi, 0), k{2});
                
                interval = get_interval(phi);
                tstart_ = extractAfter(interval, '[');
                tstart = extractBefore(tstart_, ',');
                tend_ = extractAfter(interval, ',');
                tend = extractBefore(tend_, ']');

                if ~isnan(str2double(tstart)) && ~isnan(str2double(tend))
                    this.interval_dict(strcat(phi_id, '____')) = interval;
                end

                queue = phis_';
                queue_ = [];
                row_size = numel(queue);
                col_size = 1;
                while col_size < kNum
                    for iq = 1:row_size
                        for p = phis_
                            queue_ = [queue_; queue(iq,:) p];
                        end
                    end
                    queue = queue_;
                    queue_ = [];
                    [row_size, col_size] = size(queue); 
                end

                for i = 1:row_size
                    id_ = 'PosAlw_';
                    simplified_id_ = 'PosAlw_';
                    
                    simp_fixed_false = false; %if true, whole formula = false
                    simp_exist_nontrue = false; %if true, alw(true) = true

                    phi_set = [];
                    simp_phi_set = [];
                    for j = 1:col_size
                        p_ = queue(i,j).phi;
                        p_simp_id = this.simplify_dict(get_id(p_));

                        if strcmp(p_simp_id, 'FALSE')
                            simp_fixed_false = true;
                        elseif ~strcmp(p_simp_id, 'TRUE')
                            simp_exist_nontrue = true;
                        end

                        id_loc_ = strcat('Alw', get_id(p_));

                        if j == 1
                            tst = tstart;
                        else
                            tst = strcat(phi_id, '____t', int2str(j));
                        end
                        if j == col_size
                            ted = tend;
                        else
                            ted = strcat(phi_id, '____t', int2str(j+1));
                        end
                        op_alw = strcat('alw_','[',tst ,',', ted ,']');
                        phi_loc_ = phi_merge(p_, op_alw, id_loc_);
                        id_ = strcat(id_,  get_id(p_));

                        if ~strcmp(p_simp_id, 'TRUE') && ~strcmp(p_simp_id, 'FALSE')                            
                            if j == 1
                                simplified_id_ = strcat(simplified_id_, 'st', p_simp_id);
                            elseif j == col_size
                                simplified_id_ = strcat(simplified_id_, 'ed', p_simp_id);
                            else
                                simplified_id_ = strcat(simplified_id_, p_simp_id);
                            end
                            simp_phi_set = [simp_phi_set phi_merge(this.formula_dict(p_simp_id), op_alw, id_loc_)];
                        end
                        phi_set = [phi_set, phi_loc_];
                        
                    end

                    phi_ = phi_merge(phi_set, 'aand', id_);
                    phis = [phis PhiNode(phi_)];

                    if simp_fixed_false
                        simplified_id = 'FALSE';
                        simp_phi_ = STL_Formula('FALSE', 'false');
                    elseif ~simp_exist_nontrue
                        simplified_id = 'TRUE';
                        simp_phi_ = STL_Formula('TRUE', 'true');
                    else
                        simplified_id = simplified_id_;
                        simp_phi_ = phi_merge(simp_phi_set, 'aand', simplified_id);
                    end
                    this.simplify_dict(id_) = simplified_id;
                    this.formula_dict(simplified_id) = simp_phi_;
                end
                


            elseif strcmp(get_type(phi), 'eventually')
                phi_id = get_id(phi);
                phis = [];

                kNum = k{1};
                phis_ = this.parse_nodes_pos(get_phis(phi, 0), k{2});

                interval = get_interval(phi);
                tstart_ = extractAfter(interval, '[');
                tstart = extractBefore(tstart_, ',');
                tend_ = extractAfter(interval, ',');
                tend = extractBefore(tend_, ']');

                if ~isnan(str2double(tstart)) && ~isnan(str2double(tend))
                    this.interval_dict(strcat(phi_id, '____')) = interval;
                end

                queue = phis_';
                queue_ = [];
                row_size = numel(queue);
                col_size = 1;
                while col_size < kNum
                    for iq = 1:row_size
                        for p = phis_
                            queue_ = [queue_; queue(iq,:) p];
                        end
                    end
                    queue = queue_;
                    queue_ = [];
                    [row_size, col_size] = size(queue); 
                end

                for i = 1:row_size
                    id_ = 'PosEv_';
                    simplified_id_ = 'PosEv_';

                    simp_fixed_true = false; %if true, whole formula = true
                    simp_exist_nonfalse = false; 

                    phi_set = [];
                    simp_phi_set = [];

                    for j = 1:col_size
                        p_ = queue(i,j).phi;
                        p_simp_id = this.simplify_dict(get_id(p_));
                        
                        if strcmp(p_simp_id, 'TRUE')
                            simp_fixed_true = true;
                        elseif ~strcmp(p_simp_id, 'FALSE')
                            simp_exist_nonfalse = true;
                        end
                        

                        id_loc_ = strcat('Ev', get_id(p_));

                        if j == 1
                            tst = tstart;
                        else
                            tst = strcat(phi_id, '____t', int2str(j));
                        end
                        if j == col_size
                            ted = tend;
                        else
                            ted = strcat(phi_id, '____t', int2str(j+1));
                        end
                        op_ev = strcat('ev_','[',tst ,',', ted ,']');
                        phi_loc_ = phi_merge(p_, op_ev, id_loc_);
                        id_ = strcat(id_,  get_id(p_));

                        if ~strcmp(p_simp_id, 'TRUE') && ~strcmp(p_simp_id, 'FALSE')

                            if j == 1
                                simplified_id_ = strcat(simplified_id_, 'st', p_simp_id);
                            elseif j == col_size
                                simplified_id_ = strcat(simplified_id_, 'ed', p_simp_id);
                            else
                                simplified_id_ = strcat(simplified_id_, p_simp_id);
                            end
                            simp_phi_set = [simp_phi_set phi_merge(this.formula_dict(p_simp_id), op_ev, id_loc_)];
                        end
                        phi_set = [phi_set, phi_loc_];
                    end


                    phi_ = phi_merge(phi_set, 'oor', id_);
                    phis = [phis PhiNode(phi_)];

                    if simp_fixed_true
                        simplified_id = 'TRUE';
                        simp_phi_ = STL_Formula('TRUE', 'true');
                    elseif ~simp_exist_nonfalse
                        simplified_id = 'FALSE';
                        simp_phi_ = STL_Formula('FALSE', 'false');
                    else
                        simplified_id = simplified_id_;
                        simp_phi_ = phi_merge(simp_phi_set, 'oor', simplified_id);
                    end
                    this.simplify_dict(id_) = simplified_id;
                    this.formula_dict(simplified_id) = simp_phi_;
                end
            end
        end

        function phis = parse_nodes_neg(this, phi, k)
            if strcmp(get_type(phi), 'predicate')
                phis = PhiNode(phi);
                this.simplify_dict(get_id(phi)) =  get_id(phi);
                this.formula_dict(get_id(phi)) = phi;

                t_stl = STL_Formula('TRUE', 'true');
                phis = [phis PhiNode(t_stl)];
                this.simplify_dict('TRUE') =  'TRUE';
                this.formula_dict('TRUE') = t_stl;

            elseif strcmp(get_type(phi), 'not')
                phis = [];
                phis_ = this.parse_nodes_pos(get_phis(phi, 0), k{2});

                for p = phis_
                    p_ = p.phi;

                    id_ = strcat('NegNot_', get_id(p_));
                    phi_ = phi_merge(p_, 'not', id_);
                    phis = [phis PhiNode(phi_)];
                    
                    p_simp_id = this.simplify_dict(get_id(p_));
                    if strcmp(p_simp_id, 'FALSE')
                        simplified_id = 'TRUE';
                        simp_phi_ = STL_Formula('TRUE', 'true');
                    elseif strcmp(p_simp_id, 'TRUE')
                        simplified_id = 'FALSE';
                        simp_phi_ = STL_Formula('FALSE', 'false');
                    else
                        simplified_id = strcat('NegNot_', p_simp_id);
                        simp_phi_ = phi_merge(this.formula_dict(p_simp_id), 'not', simplified_id);

                    end
                    this.simplify_dict(id_) = simplified_id;
                    this.formula_dict(simplified_id) = simp_phi_;

                end
                
            elseif strcmp(get_type(phi), 'and')
                phis = [];
                phis1 = this.parse_nodes_neg(get_phis(phi, 1), k{2});
                phis2 = this.parse_nodes_neg(get_phis(phi, 2), k{3});

                for p1 = phis1
                    for p2 = phis2
                        p1_ = p1.phi;
                        p2_ = p2.phi;

                        id_ = strcat('NegAnd_', get_id(p1_), get_id(p2_));
                        phi_ = phi_merge([p1_, p2_], 'and', id_);
                        phis = [phis PhiNode(phi_)];

                        p1_simp_id = this.simplify_dict(get_id(p1_));
                        p2_simp_id = this.simplify_dict(get_id(p2_));
                        if strcmp(p1_simp_id, 'FALSE') || strcmp(p2_simp_id, 'FALSE') 
                            simplified_id = 'FALSE';
                            simp_phi_ = STL_Formula('FALSE', 'false');
                        elseif strcmp(p1_simp_id, 'TRUE') && strcmp(p2_simp_id, 'TRUE')
                            simplified_id = 'TRUE';
                            simp_phi_ = STL_Formula('TRUE', 'true');
                        elseif strcmp(p1_simp_id, 'TRUE')
                            simplified_id = p2_simp_id;
                            simp_phi_ = this.formula_dict(p2_simp_id);
                        elseif strcmp(p2_simp_id, 'TRUE')
                            simplified_id = p1_simp_id;
                            simp_phi_ = this.formula_dict(p1_simp_id);
                        else
                            simplified_id = strcat('NegAnd_', p1_simp_id, p2_simp_id);
                            simp_phi_ = phi_merge([this.formula_dict(p1_simp_id), this.formula_dict(p2_simp_id)], 'and', simplified_id);
                        end
                        this.simplify_dict(id_) = simplified_id;
                        this.formula_dict(simplified_id) = simp_phi_;
                    end
                end
                
            elseif strcmp(get_type(phi), 'or')
                phis = [];
                phis1 = this.parse_nodes_neg(get_phis(phi, 1), k{2});
                phis2 = this.parse_nodes_neg(get_phis(phi, 2), k{3});
                for p1 = phis1
                    for p2 = phis2
                        p1_ = p1.phi;
                        p2_ = p2.phi;

                        id_ = strcat('NegOr_', get_id(p1_), get_id(p2_));
                        phi_ = phi_merge([p1_, p2_], 'or', id_);
                        phis = [phis PhiNode(phi_)];

                        p1_simp_id = this.simplify_dict(get_id(p1_));
                        p2_simp_id = this.simplify_dict(get_id(p2_));
                        if strcmp(p1_simp_id, 'TRUE') || strcmp(p2_simp_id, 'TRUE') 
                            simplified_id = 'TRUE';
                            simp_phi_ = STL_Formula('TRUE', 'true');
                        elseif strcmp(p1_simp_id, 'FALSE') && strcmp(p2_simp_id, 'FALSE')
                            simplified_id = 'FALSE';
                            simp_phi_ = STL_Formula('FALSE', 'false');
                        elseif strcmp(p1_simp_id, 'FALSE')
                            simplified_id = p2_simp_id;
                            simp_phi_ = this.formula_dict(p2_simp_id);
                        elseif strcmp(p2_simp_id, 'FALSE')
                            simplified_id = p1_simp_id;
                            simp_phi_ = this.formula_dict(p1_simp_id);
                        else
                            simplified_id = strcat('NegOr_', p1_simp_id, p2_simp_id);
                            simp_phi_ = phi_merge([this.formula_dict(p1_simp_id), this.formula_dict(p2_simp_id)], 'or', simplified_id);
                        end
                        this.simplify_dict(id_) = simplified_id;
                        this.formula_dict(simplified_id) = simp_phi_;
                    end
                end

            elseif strcmp(get_type(phi), 'always')
                phi_id = get_id(phi);
                phis = [];

                kNum = k{1};
                phis_ = this.parse_nodes_neg(get_phis(phi, 0), k{2});
                
                interval = get_interval(phi);
                tstart_ = extractAfter(interval, '[');
                tstart = extractBefore(tstart_, ',');
                tend_ = extractAfter(interval, ',');
                tend = extractBefore(tend_, ']');

                if ~isnan(str2double(tstart)) && ~isnan(str2double(tend))
                    this.interval_dict(strcat(phi_id, '____')) = interval;
                end

                queue = phis_';
                queue_ = [];
                row_size = numel(queue);
                col_size = 1;
                while col_size < kNum
                    for iq = 1:row_size
                        for p = phis_
                            queue_ = [queue_; queue(iq,:) p];
                        end
                    end
                    queue = queue_;
                    queue_ = [];
                    [row_size, col_size] = size(queue); 
                end

                for i = 1:row_size
                    id_ = 'NegAlw_';
                    simplified_id_ = 'NegAlw_';
                    
                    simp_fixed_false = false; %if true, whole formula = false
                    simp_exist_nontrue = false; %if true, alw(true) = true
                    phi_set = [];
                    simp_phi_set = [];

                    for j = 1:col_size
                        p_ = queue(i,j).phi;
                        p_simp_id = this.simplify_dict(get_id(p_));
                        
                        %%%
                        if strcmp(p_simp_id, 'FALSE')
                            simp_fixed_false = true;
                        elseif ~strcmp(p_simp_id, 'TRUE')
                            simp_exist_nontrue = true;
                        end
                        %%%

                        id_loc_ = strcat('Alw', get_id(p_));

                        if j == 1
                            tst = tstart;
                        else
                            tst = strcat(phi_id, '____t', int2str(j));
                        end
                        if j == col_size
                            ted = tend;
                        else
                            ted = strcat(phi_id, '____t', int2str(j+1));
                        end
                        op_alw = strcat('alw_','[',tst ,',', ted ,']');

                        phi_loc_ = phi_merge(p_, op_alw, id_loc_);
                        id_ = strcat(id_,  get_id(p_));

                        %%%
                        if ~strcmp(p_simp_id, 'TRUE') && ~strcmp(p_simp_id, 'FALSE')
                            if j == 1
                                simplified_id_ = strcat(simplified_id_, 'st', p_simp_id);
                            elseif j == col_size
                                simplified_id_ = strcat(simplified_id_, 'ed', p_simp_id);
                            else
                                simplified_id_ = strcat(simplified_id_, p_simp_id);
                            end
                            simp_phi_set = [simp_phi_set phi_merge(this.formula_dict(p_simp_id), op_alw, id_loc_)];
                        end
                        %%%
                        phi_set = [phi_set, phi_loc_];
                        
                    end


                    phi_ = phi_merge(phi_set, 'aand', id_);
                    phis = [phis PhiNode(phi_)];
                    
                    %%%
                    if simp_fixed_false
                        simplified_id = 'FALSE';
                        simp_phi_ = STL_Formula('FALSE', 'false');
                    elseif ~simp_exist_nontrue
                        simplified_id = 'TRUE';
                        simp_phi_ = STL_Formula('TRUE', 'true');
                    else
                        simplified_id = simplified_id_;
                        simp_phi_ = phi_merge(simp_phi_set, 'aand', simplified_id);
                    end
                    this.simplify_dict(id_) = simplified_id;
                    this.formula_dict(simplified_id) = simp_phi_;

                end

            elseif strcmp(get_type(phi), 'eventually')
                phi_id = get_id(phi);
                phis = [];

                kNum = k{1};
                phis_ = this.parse_nodes_neg(get_phis(phi, 0), k{2});

                interval = get_interval(phi);
                tstart_ = extractAfter(interval, '[');
                tstart = extractBefore(tstart_, ',');
                tend_ = extractAfter(interval, ',');
                tend = extractBefore(tend_, ']');

                if ~isnan(str2double(tstart)) && ~isnan(str2double(tend))
                    this.interval_dict(strcat(phi_id, '____')) = interval;
                end

                queue = phis_';
                queue_ = [];
                row_size = numel(queue);
                col_size = 1;
                while col_size < kNum
                    for iq = 1:row_size
                        for p = phis_
                            queue_ = [queue_; queue(iq,:) p];
                        end
                    end
                    queue = queue_;
                    queue_ = [];
                    [row_size, col_size] = size(queue); 
                end

                for i = 1:row_size
                    id_ = 'NegEv_';
                    simplified_id_ = 'NegEv_';
                    
                    simp_fixed_true = false; %if true, whole formula = true
                    simp_exist_nonfalse = false; 

                    phi_set = [];
                    simp_phi_set = [];

                    for j = 1:col_size
                        p_ = queue(i,j).phi;
                        p_simp_id = this.simplify_dict(get_id(p_));
                        %%%
                        if strcmp(p_simp_id, 'TRUE')
                            simp_fixed_true = true;
                        elseif ~strcmp(p_simp_id, 'FALSE')
                            simp_exist_nonfalse = true;
                        end
                        %%%

                        id_loc_ = strcat('Ev', get_id(p_));

                        if j == 1
                            tst = tstart;
                        else
                            tst = strcat(phi_id, '____t', int2str(j));
                        end
                        if j == col_size
                            ted = tend;
                        else
                            ted = strcat(phi_id, '____t', int2str(j+1));
                        end
                        op_ev = strcat('ev_','[',tst ,',', ted ,']');

                        phi_loc_ = phi_merge(p_, op_ev, id_loc_);
                        id_ = strcat(id_,  get_id(p_));

                        %%%
                        if ~strcmp(p_simp_id, 'TRUE') && ~strcmp(p_simp_id, 'FALSE')
                            if j == 1
                                simplified_id_ = strcat(simplified_id_, 'st', p_simp_id);
                            elseif j == col_size
                                simplified_id_ = strcat(simplified_id_, 'ed', p_simp_id);
                            else
                                simplified_id_ = strcat(simplified_id_, p_simp_id);
                            end
                            simp_phi_set = [simp_phi_set phi_merge(this.formula_dict(p_simp_id), op_ev, id_loc_)];
                        end
                        %%%
                        phi_set = [phi_set, phi_loc_];
                    end

                    phi_ = phi_merge(phi_set, 'oor', id_);
                    phis = [phis PhiNode(phi_)];
                    
                    if simp_fixed_true
                        simplified_id = 'TRUE';
                        simp_phi_ = STL_Formula('TRUE', 'true');
                    elseif ~simp_exist_nonfalse
                        simplified_id = 'FALSE';
                        simp_phi_ = STL_Formula('FALSE', 'false');
                    else
                        simplified_id = simplified_id_;
                        simp_phi_ = phi_merge(simp_phi_set, 'oor', simplified_id);
                    end
                    this.simplify_dict(id_) = simplified_id;
                    this.formula_dict(simplified_id) = simp_phi_;
                end
            end

        end

        function rels = parse_edges_pos(this, phi, k)
            if strcmp(get_type(phi), 'predicate')
                id = get_id(phi);
                rels = [PhiEdge(id, id)];
                rels = [rels PhiEdge(id, 'FALSE')];
                rels = [rels PhiEdge('FALSE', 'FALSE')];

            elseif strcmp(get_type(phi), 'not')
                rels = [];
                rels_ = this.parse_edges_neg(get_phis(phi, 0), k{2});
                for r = rels_
                    id1 = strcat('PosNot_', r.greater);
                    id2 = strcat('PosNot_', r.smaller);
                    rels = [rels PhiEdge(id1, id2)];
                end

            elseif strcmp(get_type(phi), 'or')
                rels = [];
                rels1 = this.parse_edges_pos(get_phis(phi, 1), k{2});
                rels2 = this.parse_edges_pos(get_phis(phi, 2), k{3});
                for r1 = rels1
                    for r2 = rels2
                        id1 = strcat('PosOr_', r1.greater, r2.greater);
                        id2 = strcat('PosOr_', r1.smaller, r2.smaller);
                        rels = [rels PhiEdge(id1, id2)];
                    end
                end
             

            elseif strcmp(get_type(phi), 'and')
                rels = [];
                rels1 = this.parse_edges_pos(get_phis(phi, 1), k{2});
                rels2 = this.parse_edges_pos(get_phis(phi, 2), k{3});
                for r1 = rels1
                    for r2 = rels2
                        id1 = strcat('PosAnd_', r1.greater, r2.greater);
                        id2 = strcat('PosAnd_', r1.smaller, r2.smaller);
                        rels = [rels PhiEdge(id1, id2)];
                    end
                end

            elseif strcmp(get_type(phi), 'eventually')
                rels = [];
                kNum = k{1};
                rels_ = this.parse_edges_pos(get_phis(phi, 0), k{2});
                
                queue = rels_';
                queue_ = [];
                row_size = numel(queue);
                col_size = 1;
                while col_size < kNum
                    for iq = 1:row_size
                        for p = rels_
                            queue_ = [queue_; queue(iq,:) p];
                        end
                    end
                    queue = queue_;
                    queue_ = [];
                    [row_size, col_size] = size(queue);
                end

                for i = 1:row_size
                    id_1 = 'PosEv_';
                    id_2 = 'PosEv_';
                    for j = 1:col_size
                        r = queue(i,j);
                        id_1 = strcat(id_1, r.greater);
                        id_2 = strcat(id_2, r.smaller);
                    end
                    rels = [rels PhiEdge(id_1, id_2)];
                end

            elseif strcmp(get_type(phi), 'always')
                rels = [];
                kNum = k{1};
                rels_ = this.parse_edges_pos(get_phis(phi, 0), k{2});
                
                queue = rels_';
                queue_ = [];
                row_size = numel(queue);
                col_size = 1;
                while col_size < kNum
                    for iq = 1:row_size
                        for p = rels_
                            queue_ = [queue_; queue(iq,:) p];
                        end
                    end
                    queue = queue_;
                    queue_ = [];
                    [row_size, col_size] = size(queue);
                end

                for i = 1:row_size
                    id_1 = 'PosAlw_';
                    id_2 = 'PosAlw_';
                    for j = 1:col_size
                        r = queue(i,j);
                        id_1 = strcat(id_1, r.greater);
                        id_2 = strcat(id_2, r.smaller);
                    end
                    rels = [rels PhiEdge(id_1, id_2)];
                end
            end
        end

        function rels = parse_edges_neg(this, phi, k)
            if strcmp(get_type(phi), 'predicate')
                id = get_id(phi);
                rels = [PhiEdge(id, id)];
                rels = [rels PhiEdge(id, 'TRUE')];
                rels = [rels PhiEdge('TRUE', 'TRUE')];

            elseif strcmp(get_type(phi), 'not')
                rels = [];
                rels_ = this.parse_edges_pos(get_phis(phi, 0), k{2});
                for r = rels_
                    id1 = strcat('NegNot_', r.greater);
                    id2 = strcat('NegNot_', r.smaller);
                    rels = [rels PhiEdge(id1, id2)];
                end
            elseif strcmp(get_type(phi), 'or')
                rels = [];
                rels1 = this.parse_edges_neg(get_phis(phi, 1), k{2});
                rels2 = this.parse_edges_neg(get_phis(phi, 2), k{3});
                for r1 = rels1
                    for r2 = rels2
                        id1 = strcat('NegOr_', r1.greater, r2.greater);
                        id2 = strcat('NegOr_', r1.smaller, r2.smaller);
                        rels = [rels PhiEdge(id1, id2)];
                    end
                end

            elseif strcmp(get_type(phi), 'and')
                rels = [];
                rels1 = this.parse_edges_neg(get_phis(phi, 1));
                rels2 = this.parse_edges_neg(get_phis(phi, 2));
                for r1 = rels1
                    for r2 = rels2
                        id1 = strcat('NegAnd_', r1.greater, r2.greater);
                        id2 = strcat('NegAnd_', r1.smaller, r2.smaller);
                        rels = [rels PhiEdge(id1, id2)];
                    end
                end

            elseif strcmp(get_type(phi), 'eventually')
                rels = [];
                kNum = k{1};
                rels_ = this.parse_edges_neg(get_phis(phi, 0), k{2});
                
                queue = rels_';
                queue_ = [];
                row_size = numel(queue);
                col_size = 1;
                while col_size < kNum
                    for iq = 1:row_size
                        for p = rels_
                            queue_ = [queue_; queue(iq,:) p];
                        end
                    end
                    queue = queue_;
                    queue_ = [];
                    [row_size, col_size] = size(queue);
                end

                for i = 1:row_size
                    id_1 = 'NegEv_';
                    id_2 = 'NegEv_';
                    for j = 1:col_size
                        r = queue(i,j);
                        id_1 = strcat(id_1, r.greater);
                        id_2 = strcat(id_2, r.smaller);
                    end
                    rels = [rels PhiEdge(id_1, id_2)];
                end

            elseif strcmp(get_type(phi), 'always')
                rels = [];
                kNum = k{1};
                rels_ = this.parse_edges_neg(get_phis(phi, 0), k{2});
                
                queue = rels_';
                queue_ = [];
                row_size = numel(queue);
                col_size = 1;
                while col_size < kNum
                    for iq = 1:row_size
                        for p = rels_
                            queue_ = [queue_; queue(iq,:) p];
                        end
                    end
                    queue = queue_;
                    queue_ = [];
                    [row_size, col_size] = size(queue);
                end

                for i = 1:row_size
                    id_1 = 'NegAlw_';
                    id_2 = 'NegAlw_';
                    for j = 1:col_size
                        r = queue(i,j);
                        id_1 = strcat(id_1, r.greater);
                        id_2 = strcat(id_2, r.smaller);
                    end
                    rels = [rels PhiEdge(id_1, id_2)];
                end
            end
        end


    end

end