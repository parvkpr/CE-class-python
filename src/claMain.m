% fuel_inj_tol = 1.0; 
% MAF_sensor_tol = 1.0; 
% AF_sensor_tol = 1.0; 
% pump_tol = 1.; 
% kappa_tol=1; 
% tau_ww_tol=1; 
% fault_time=50;
% kp = 0.04;
% ki = 0.14;
% 
% mdl = 'AbstractFuelControl_M1';
% Br = BreachSimulinkSystem(mdl);
% Br.Sys.tspan =0:.01:50;
% input_gen.type = 'UniStep';
% input_gen.cp = 5;
% Br.SetInputGen(input_gen);
% u = [1000 1000 1000 1000 1000 15 20 15 15 15];
% for cpi = 0:input_gen.cp-1
%     ES_sig = strcat('Engine_Speed_u', num2str(cpi));
%     PA_sig = strcat('Pedal_Angle_u', num2str(cpi));
% 
%     Br.SetParam({ES_sig},u(cpi+1));
%     Br.SetParam({PA_sig},u(cpi + input_gen.cp + 1));
% end
% Br.Sim(0:.01:50);

mdl = 'Autotrans_shift';
Br = BreachSimulinkSystem(mdl);
Br.Sys.tspan =0:.01:30;
input_gen.type = 'UniStep';
input_gen.cp = 5;
Br.SetInputGen(input_gen);
u = [96.5415 146.2275 10.9136 258.6729 325.0000 90.0002 56.6638 3.4367 86.1157 0 ];
for cpi = 0:input_gen.cp-1
    brake_sig = strcat('brake_u', num2str(cpi));
    throttle_sig = strcat('throttle_u', num2str(cpi));

    Br.SetParam({brake_sig},u(cpi+1));
    Br.SetParam({throttle_sig},u(cpi + input_gen.cp + 1));
end
Br.Sim(0:.01:10);

%spec = 'ev_[0,40](alw_[0,10](AF[t] - AFref[t] < 0.05 and AF[t] - AFref[t] > -0.05))';
%spec = 'alw_[0.0, 30.0](speed[t] < 90.0 and RPM[t] < 4000)';
spec = 'alw_[0.0, 30.0](speed[t] < 80.0 and RPM[t] < 2000)';
phi = STL_Formula('phi',spec);
robust = Br.CheckSpec(phi)
trials = 1;
filename = 'Autotrans_shift_breach_AT1';
algorithm = 'Diversity';
falsified = [];
time = [];
obj_best = [];
num_sim = [];
total_nodes = [];
remained_nodes = [];
%k = {1, {0, {0}, {0}}};
%k = {2, {1, {0, {0}, {0}}}};
k = {2, {0, {0}, {0}}};

for n = 1:trials
    %syn_pb = MyClassProblemNoPrune(Br, phi, k);
    %syn_pb = MyClassProblemAlwMid(Br, phi, k);
    %syn_pb = MyClassProblemBSRandom(Br, phi, k);
    syn_pb = MyClassProblemLongBS(Br, phi, k);
    syn_pb.max_time = 5;
    syn_pb.setup_solver('cmaes');
    syn_pb.solve();
end
% spec = {spec};
% filename = {filename};
% result = table(filename, spec, falsified, time, num_sim, obj_best, total_nodes, remained_nodes);
% writetable(result,'$csv','Delimiter',';');