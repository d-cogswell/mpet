function animate(t,cpcs,ffvec,vvec,disc,part,fig,output)
%ANIMATE animation script for simulation result including surface
%potential/concentration
%   parameter fig:
%       s   show concentrations in solid
%       p   show surface concentration
%       d   plot solid concentrations along with electrode potential
%   parameter output: 
%       0   don't save animation
%       otherwise save avi file to file specified by output.

% close all
tlen = max(size(t));
numpart = max(size(part.steps))-1;

Nx = disc.Nx;
Ny = disc.numpart;
ss = disc.ss;
ssx = disc.ss / Ny;

e = 1.6e-19;
k = 1.381e-23;
T = 298;
% vvec = 3.422-cpcs(:,end)*(k*T/e);

% First let's break down the cpcs vector
% c = zeros(tlen,Ny,ssx+Nx);
% for i=1:tlen
%     c(i,:,:) = reshape(cpcs(i,1:ss+Nx*Ny),Ny,ssx+Nx);
% end

% phi = zeros(tlen,Ny,ssx+Nx);
cs = cell(numpart,1);
phis = cell(numpart,1);
% Put each particle in its own entry in a cell array
for i=1:numpart
    % Get the indices
    ind1 = sum(part.steps(1:i))+1;
    ind2 = sum(part.steps(1:i+1));
    cstmp = zeros(tlen,part.steps(i+1));
    phistmp = zeros(tlen,part.steps(i+1));
    for j=1:tlen
        cstmp(j,1:end) = cpcs(j,disc.sol+ind1-1:disc.sol+ind2-1);
        phistmp(j,1:end) = cpcs(j,disc.sol+disc.Nx+disc.ssteps+ind1-1:disc.sol+disc.ssteps+disc.Nx+ind2-1);
    end
    cs{i} = cstmp;
    phis{i} = phistmp;
end

if strcmp(fig,'s')
    scrsz = get(0,'ScreenSize');
    figure('OuterPosition',[3/4 scrsz(4)/2 3*scrsz(3)/4 scrsz(4)/2])
    for i=1:tlen
        for j=1:Nx
            for k=1:Ny
                ind = (j-1)*Ny+k;
                subplot(Ny,Nx,ind)
                sz = size(cs{ind});
                plot(cs{ind}(i,:))
                axis([1 sz(2) 0 1])
            end 
        end
        M(i) = getframe(gcf);
    end   
    implay(M);
   
elseif strcmp(fig,'p')
    scrsz = get(0,'ScreenSize');
    figure('OuterPosition',[1 scrsz(4)/4 3*scrsz(3)/4 3*scrsz(4)/4])
    for i=1:tlen
        for j=1:Nx
            for k=1:Ny
                ind = (j-1)*Ny+k;
                subplot(Ny,Nx,ind)
                sz = size(cs{ind});
                plot(phis{ind}(i,:))
                axis([1 sz(2) 0 1.1e-4]) % the last value has to be adjusted if started with a different concentration
            end 
        end
        M(i) = getframe(gcf);
    end   
    implay(M);
    
% elseif strcmp(fig,'e')
%     figure
%     for i=1:tlen
%         surf(squeeze(c(i,:,:)))
%         axis([0 ssx+Nx 0 Ny 0 1])
%         M(i) = getframe(gcf);
%     end

    
elseif strcmp(fig,'d')
    scrsz = get(0,'ScreenSize');
    figure('OuterPosition',[3/4 scrsz(4)/2 3*scrsz(3)/4 scrsz(4)/2])
    for i=1:tlen
        for j=1:Nx
            for k=1:Ny
                ind = (j-1)*Ny+k;
                sp = (k-1)*2*Nx+j;
                subplot(Ny,Nx*2,sp)
                sz = size(cs{ind});
                plot(cs{ind}(i,:))
                axis([0 sz(2) 0 1])
            end 
        end
        % Now the voltage
        subplot(Nx,Ny*2,[Ny+1 2*Ny*Nx])
        plot(ffvec,vvec)
        hold on
        plot(ffvec(i),vvec(i),'ro')
        M(i) = getframe(gcf);
        cla
    end
end

if output ~= 0 
    movie2avi(M,output)
end

return;
