spec = 5; %1: AT1, 2: AT2, 3: AFC1 4:AT3

if spec == 1
    mdl = 'Autotrans_shift';
    Br = BreachSimulinkSystem(mdl);
    Br.Sys.tspan =0:.01:30;
    input_gen.type = 'UniStep';
    input_gen.cp = 5;
    Br.SetInputGen(input_gen);
    %u = [96.5415 146.2275 10.9136 258.6729 325.0000 90.0002 56.6638 3.4367 86.1157 0 ];
    input_range = [0 325;0 100];
    input_num = 2;

    volume = 30;
    iv = 0;
    brs = [];
    while true
        u = [];
        for i = 1:input_num
            for j = 1:input_gen.cp
                val = input_range(i,1) + rand*(input_range(i,2)-input_range(i,1));
                u = [u val];
            end
        end
    
        for cpi = 0:input_gen.cp-1
            brake_sig = strcat('brake_u', num2str(cpi));
            throttle_sig = strcat('throttle_u', num2str(cpi));
        
            Br.SetParam({brake_sig},u(cpi+1));
            Br.SetParam({throttle_sig},u(cpi + input_gen.cp + 1));
        end
        Br.Sim(0:.01:30);
        
        spec = 'alw_[0.0, 30.0](speed[t] < 90.0 and RPM[t] < 4000)';
        phi = STL_Formula('phi',spec);

%         s1 = STL_Formula('a', 'alw_[0,30](speed[t] < 90)');
%         s2 = STL_Formula('a', 'alw_[0,30](RPM[t] < 4000)');
        robust = Br.CheckSpec(phi)

%         r1 = Br.CheckSpec(s1)
%         r2 = Br.CheckSpec(s2)
       
        if robust < 0
            iv = iv + 1;
            brs = [brs; u];
        end

        if iv >= volume
            save('data/AT1.mat', 'brs');
            break
        end
    end

elseif spec == 2

    mdl = 'Autotrans_shift';
    Br = BreachSimulinkSystem(mdl);
    Br.Sys.tspan =0:.01:30;
    input_gen.type = 'UniStep';
    input_gen.cp = 5;
    Br.SetInputGen(input_gen);
    %u = [96.5415 146.2275 10.9136 258.6729 325.0000 90.0002 56.6638 3.4367 86.1157 0 ];
    input_range = [0 325;0 100];
    input_num = 2;

    volume = 30;
    iv = 0;
    brs = [];
    while true
        u = [];
        for i = 1:input_num
            for j = 1:input_gen.cp
                val = input_range(i,1) + rand*(input_range(i,2)-input_range(i,1));
                u = [u val];
            end
        end
    
        for cpi = 0:input_gen.cp-1
            brake_sig = strcat('brake_u', num2str(cpi));
            throttle_sig = strcat('throttle_u', num2str(cpi));
        
            Br.SetParam({brake_sig},u(cpi+1));
            Br.SetParam({throttle_sig},u(cpi + input_gen.cp + 1));
        end
        Br.Sim(0:.01:30);
        
        spec = 'alw_[0,30](not (brake[t] > 250) or ev_[0,5](speed[t] < 30 and RPM[t] < 2000))';
        phi = STL_Formula('phi',spec);
        robust = Br.CheckSpec(phi)
       
        if robust < 0
            iv = iv + 1;
            brs = [brs;u];
        end

        if iv >= volume
            save('data/AT2.mat', 'brs');
            break
        end
    end

elseif spec == 3
    fuel_inj_tol = 1.0; 
    MAF_sensor_tol = 1.0; 
    AF_sensor_tol = 1.0; 
    pump_tol = 1.; 
    kappa_tol=1; 
    tau_ww_tol=1; 
    fault_time=50;
    kp = 0.04;
    ki = 0.14;

    mdl = 'AbstractFuelControl_M1';
    Br = BreachSimulinkSystem(mdl);
    Br.Sys.tspan =0:.01:50;
    input_gen.type = 'UniStep';
    input_gen.cp = 5;
    Br.SetInputGen(input_gen);
    %u = [96.5415 146.2275 10.9136 258.6729 325.0000 90.0002 56.6638 3.4367 86.1157 0 ];
    input_range = [900 1100;8.8 70];
    input_num = 2;

    volume = 30;
    iv = 0;
    brs = [];
    while true
        u = [];
        for i = 1:input_num
            for j = 1:input_gen.cp
                val = input_range(i,1) + rand*(input_range(i,2)-input_range(i,1));
                u = [u val];
            end
        end
    
        for cpi = 0:input_gen.cp-1
            ES_sig = strcat('Engine_Speed_u', num2str(cpi));
            PA_sig = strcat('Pedal_Angle_u', num2str(cpi));
        
            Br.SetParam({ES_sig},u(cpi+1));
            Br.SetParam({PA_sig},u(cpi + input_gen.cp + 1));
        end
        Br.Sim(0:.01:50);
        
        spec = 'ev_[0,40](alw_[0,10](AF[t] - AFref[t] < 0.05 and AF[t] - AFref[t] > -0.05))';
        phi = STL_Formula('phi',spec);
        robust = Br.CheckSpec(phi)
       
        if robust < 0
            iv = iv + 1;
            brs = [brs;u];
        end

        if iv >= volume
            save('data/AFC1.mat', 'brs');
            break
        end
    end

elseif spec == 4
    mdl = 'Autotrans_shift';
    Br = BreachSimulinkSystem(mdl);
    Br.Sys.tspan =0:.01:30;
    input_gen.type = 'UniStep';
    input_gen.cp = 5;
    Br.SetInputGen(input_gen);
    %u = [96.5415 146.2275 10.9136 258.6729 325.0000 90.0002 56.6638 3.4367 86.1157 0 ];
    input_range = [0 325;0 100];
    input_num = 2;

    volume = 30;
    iv = 0;
    brs = [];
    while true
        u = [];
        for i = 1:input_num
            for j = 1:input_gen.cp
                val = input_range(i,1) + rand*(input_range(i,2)-input_range(i,1));
                u = [u val];
            end
        end
    
        for cpi = 0:input_gen.cp-1
            brake_sig = strcat('brake_u', num2str(cpi));
            throttle_sig = strcat('throttle_u', num2str(cpi));
        
            Br.SetParam({brake_sig},u(cpi+1));
            Br.SetParam({throttle_sig},u(cpi + input_gen.cp + 1));
        end
        Br.Sim(0:.01:30);
        
        spec = 'alw_[0.0, 30.0](speed[t] < 100)';
        phi = STL_Formula('phi',spec);

%         s1 = STL_Formula('a', 'alw_[0,30](speed[t] < 90)');
%         s2 = STL_Formula('a', 'alw_[0,30](RPM[t] < 4000)');
        robust = Br.CheckSpec(phi)

%         r1 = Br.CheckSpec(s1)
%         r2 = Br.CheckSpec(s2)
       
        if robust < 0
            iv = iv + 1;
            brs = [brs; u];
        end

        if iv >= volume
            save('data/AT3.mat', 'brs');
            break
        end
    end

elseif spec == 5
    mdl = 'Autotrans_shift';
    Br = BreachSimulinkSystem(mdl);
    Br.Sys.tspan =0:.01:30;
    input_gen.type = 'UniStep';
    input_gen.cp = 5;
    Br.SetInputGen(input_gen);
    %u = [96.5415 146.2275 10.9136 258.6729 325.0000 90.0002 56.6638 3.4367 86.1157 0 ];
    input_range = [0 325;0 100];
    input_num = 2;

    volume = 30;
    iv = 0;
    brs = [];
    while true
        u = [];
        for i = 1:input_num
            for j = 1:input_gen.cp
                val = input_range(i,1) + rand*(input_range(i,2)-input_range(i,1));
                u = [u val];
            end
        end

        for cpi = 0:input_gen.cp-1
            brake_sig = strcat('brake_u', num2str(cpi));
            throttle_sig = strcat('throttle_u', num2str(cpi));

            Br.SetParam({brake_sig},u(cpi+1));
            Br.SetParam({throttle_sig},u(cpi + input_gen.cp + 1));
        end
        Br.Sim(0:.01:30);

        spec = 'ev_[0,30](speed[t] > 70 and RPM[t] > 3800)';
        phi = STL_Formula('phi',spec);
        robust = Br.CheckSpec(phi)

        if robust < 0
            iv = iv + 1;
            brs = [brs;u];
        end

        if iv >= volume
            save('data/AT53.mat', 'brs');
            break
        end
    end

end

