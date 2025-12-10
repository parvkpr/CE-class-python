classdef PhiEdge < handle
    properties
        greater
        smaller
    end

    methods
        function this = PhiEdge(g, s)
            this.greater = g;
            this.smaller = s;
        end
    end

end