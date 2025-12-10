function phi = phi_merge(phis, type, id)
    if isa(id, 'string')
        id = convertStringsToChars(id);
    end
    if startsWith(type, 'and')
        phi = STL_Formula(id, strcat('(', disp(phis(1)), ') and (', disp(phis(2)), ')'));
    elseif startsWith(type, 'or')
        phi = STL_Formula(id, strcat('(', disp(phis(1)), ') or (', disp(phis(2)), ')'));
    elseif startsWith(type, 'not')
        phi = STL_Formula(id, strcat('not(', disp(phis) ,')'));
    elseif startsWith(type, 'alw')
        phi = STL_Formula(id, strcat(type, '(', disp(phis), ')'));
    elseif startsWith(type, 'ev')
        phi = STL_Formula(id, strcat(type, '(', disp(phis), ')'));
    elseif startsWith(type, 'aand')
        str = '(';
        for i = 1: numel(phis)
            str = strcat(str, disp(phis(i)));
            if i ~= numel(phis)
                str = strcat(str, ') and (');
            end
        end
        str = strcat(str, ')');
        phi = STL_Formula(id, str);
    elseif startsWith(type, 'oor')
        str = '(';
        for i = 1: numel(phis)
            str = strcat(str, disp(phis(i)));
            if i ~= numel(phis)
                str = strcat(str, ') or (');
            end
        end
        str = strcat(str, ')');
        phi = STL_Formula(id, str);
    else
        phi = [];
    end
end