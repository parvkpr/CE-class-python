addpath(genpath('/home/zhenya/CEClassification'))
load('data/AFC1.mat', 'brs');

fuel_inj_tol = 1.0; 
MAF_sensor_tol = 1.0; 
AF_sensor_tol = 1.0; 
pump_tol = 1.; 
kappa_tol=1; 
tau_ww_tol=1; 
fault_time=50;
kp = 0.04;
ki = 0.14;

numclass = [];
numcovered = [];
totaltime = [];
timeSplit = [];
timeClass = [];
%avgtimesignal = [];

%k = {1, {1, {0, {0}, {0}}}};
% ks = {{1, {1, {0, {0}, {0}}}}, ...
%     {2, {1, {0, {0}, {0}}}}, ...
%     {3, {1, {0, {0}, {0}}}}, ...
%     {4, {1, {0, {0}, {0}}}}, ...
%     {5, {1, {0, {0}, {0}}}}};
ks = {{1, {1, {0, {0}, {0}}}}, ...
    {2, {1, {0, {0}, {0}}}}, ...
    {3, {1, {0, {0}, {0}}}}, ...
    {4, {1, {0, {0}, {0}}}}};
spec = 'ev_[0,40](alw_[0,10](AF[t] - AFref[t] < 0.05 and AF[t] - AFref[t] > -0.05))';
phi = STL_Formula('phi',spec);

% coarse
AnotB = [];
BnotA = [];

%fine
CnotD = [];
DnotC = [];

[rowsize, colsize] = size(brs);

for ik = 1:numel(ks)
    numclass = 0;
    numcovered = 0;
    totaltime = 0;
    timeSplit = 0;
    timeClass = 0;
    res_dict = dictionary;

    for ibr = 1:rowsize
        
        mdl = 'AbstractFuelControl_M1';
        Br = BreachSimulinkSystem(mdl);
        Br.Sys.tspan =0:.01:50;
        input_gen.type = 'UniStep';
        input_gen.cp = 5;
        Br.SetInputGen(input_gen);
        %u = [1000 1000 1000 1000 1000 15 20 15 15 15];
        inp = brs(ibr, :);
        for cpi = 0:input_gen.cp-1
            ES_sig = strcat('Engine_Speed_u', num2str(cpi));
            PA_sig = strcat('Pedal_Angle_u', num2str(cpi));
        
            Br.SetParam({ES_sig},inp(cpi+1));
            Br.SetParam({PA_sig},inp(cpi + input_gen.cp + 1));
        end
        Br.Sim(0:.01:50);

        syn_pb = MyClassProblemNoPrune(Br, phi, ks{ik});
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
    filename = strcat('AFC1_', num2str(ik), '.csv');
    writetable(result,filename,'Delimiter',';');

end




% result = table(filename, spec, falsified, time, num_sim, obj_best, total_nodes, remained_nodes);
% writetable(result,'$csv','Delimiter',';');
