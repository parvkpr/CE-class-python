mdl = 'Autotrans_shift';
Br = BreachSimulinkSystem(mdl);
Br.Sys.tspan =0:.01:30;
input_gen.type = 'UniStep';
input_gen.cp = 5;
Br.SetInputGen(input_gen);
for cpi = 0:input_gen.cp -1
    throttle_sig = strcat('throttle_u',num2str(cpi));
    Br.SetParamRanges({throttle_sig},[0.0 100.0]);
    brake_sig = strcat('brake_u',num2str(cpi));
    Br.SetParamRanges({brake_sig},[0.0 325.0]);
end

spec = 'alw_[0.0, 30.0](speed[t] < 80.0 and RPM[t] < 2000)';
phi = STL_Formula('phi',spec);
trials = 1;
filename = 'Autotrans_shift_breach_AT1';
algorithm = 'Diversity';
falsified = [];
time = [];
obj_best = [];
num_sim = [];
total_nodes = [];
remained_nodes = [];

for n = 1:trials
    falsif_pb = MyFP(Br,phi);
    falsif_pb.max_time = 50;
    falsif_pb.setup_solver('cmaes');
    falsif_pb.solve();
    if falsif_pb.obj_best < 0
        falsified = [falsified;1];
    else
        falsified = [falsified;0];
    end
    num_sim = [num_sim;falsif_pb.nb_obj_eval];
    time = [time;falsif_pb.time_spent];
    obj_best = [obj_best;falsif_pb.obj_best];
    total_nodes = [total_nodes;falsif_pb.num_total_nodes];
    remained_nodes = [remained_nodes; falsif_pb.num_remained_nodes];
end
spec = {spec};
filename = {filename};
result = table(filename, spec, falsified, time, num_sim, obj_best, total_nodes, remained_nodes);
writetable(result,'$csv','Delimiter',';');