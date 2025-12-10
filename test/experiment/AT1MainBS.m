addpath(genpath('/home/zhenya/CEClassification'))
load('data/AT1.mat', 'brs');

%ks = {{1, {0, {0}, {0}}}, {2, {0, {0}, {0}}},{3, {0, {0}, {0}}},{4, {0, {0}, {0}}},{5, {0, {0}, {0}}}};
ks = {{1, {0, {0}, {0}}}, {2, {0, {0}, {0}}},{3, {0, {0}, {0}}},{4, {0, {0}, {0}}}};
spec = 'alw_[0.0, 30.0](speed[t] < 90.0 and RPM[t] < 4000)';
phi = STL_Formula('phi',spec);

AnotB = [];
BnotA = [];

[rowsize, colsize] = size(brs);
% u = [96.5415 146.2275 10.9136 258.6729 325.0000 90.0002 56.6638 3.4367 86.1157 0 ];

for ik = 1:numel(ks)
    numclass = 0;
    numcovered = 0;
    totaltime = 0;
    timeSplit = 0;
    timeClass = 0;
    res_dict = dictionary;

    for ibr = 1: rowsize
        mdl = 'Autotrans_shift';
        Br = BreachSimulinkSystem(mdl);
        Br.Sys.tspan =0:.01:30;
        input_gen.type = 'UniStep';
        input_gen.cp = 5;
        Br.SetInputGen(input_gen);

        inp = brs(ibr, :);
        for cpi = 0:input_gen.cp-1
            brake_sig = strcat('brake_u', num2str(cpi));
            throttle_sig = strcat('throttle_u', num2str(cpi));
        
            Br.SetParam({brake_sig},inp(cpi+1));
            Br.SetParam({throttle_sig},inp(cpi + input_gen.cp + 1));
        end
        Br.Sim(0:.01:30);

        syn_pb = MyClassProblemAlwMid(Br, phi, ks{ik});
        syn_pb.max_time = 20;
        syn_pb.setup_solver('cmaes');
        syn_pb.solve();
        

        if ibr == 1
            numclass = syn_pb.numclass;
            for nd = syn_pb.graph.nodes
                if numel(nd.results) ~= 0
                    res_dict(nd.get_phi_id()) = 1;
                else
                    res_dict(nd.get_phi_id()) = 0;
                end
            end
            timeSplit = timeSplit + syn_pb.timeSplit;
            totaltime = totaltime + syn_pb.totaltime;
        else
            for nd = syn_pb.graph.nodes
                if numel(nd.results) ~= 0
                    res_dict(nd.get_phi_id()) = res_dict(nd.get_phi_id()) + 1;
                end
            end
            totaltime = totaltime + syn_pb.timeClass;
        end
        timeClass = timeClass + syn_pb.timeClass;

    end
    
    vs = values(res_dict);
    for vvi = 1:numel(vs)
        if vs(vvi) > 0
            numcovered = numcovered + 1;
        end
    end

    result = table(numclass, numcovered, totaltime, timeSplit, timeClass);
    filename = strcat('BS_AT1_', num2str(ik), '.csv');
    writetable(result,filename,'Delimiter',';');

end




% result = table(filename, spec, falsified, time, num_sim, obj_best, total_nodes, remained_nodes);
% writetable(result,'$csv','Delimiter',';');
