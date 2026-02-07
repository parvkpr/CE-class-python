This repository is for the artifact evaluation of the paper "Counterexample Classification against Signal Temporal Logic Specifications" submitted to FM 2026.

## System requirement

- Operating system: Linux or MacOS;

- Matlab (Simulink/Stateflow) version: >= 2022a. (Matlab license needed)

- Python version: >= 3.7

## Installation

- Clone the repository.
  1. `git clone https://github.com/choshina/CEClass.git`
  2. `git submodule init`
  3. `git submodule update`

- Install [Breach](https://github.com/decyphir/breach).
  1. start matlab, set up a C/C++ compiler using the command `mex -setup`. (Refer to [here](https://www.mathworks.com/help/matlab/matlab_external/changing-default-compiler.html) for more details.)
  2. navigate to `breach/` in Matlab commandline, and run `InstallBreach`

- Install the tool as follows
  1. in terminal navigate to the project home, and run `sh Install.sh`

***
## Reproduce the Results in Paper

### Effectiveness evaluation
- navigate to `test/experiment/`
- Find the scripts ending with "plot.m", and plot the results by running these scripts.

### Efficiency evaluation
- navigate to `test/experiment/`
  > in this directory, there are a number of Matlab scripts. The scripts ending with "Main.m" are the baseline approaches, while the scripts ending with "MainBS.m" are the proposed approaches
- select a script and run it in Matlab commandline.

## Structure of the repository

```
├── Install.sh
├── LICENSE
├── README.md
├── breach
├── model
├── src
│   ├── MyClassProblem.m
│   ├── MyClassProblemAlwMid.m
│   ├── MyClassProblemBSRandom.m
│   ├── MyClassProblemLongBS.m
│   ├── MyClassProblemNoPrune.m
│   ├── MyFP.m
│   ├── MyParamSynthProblem.m
│   ├── Parser.m
│   ├── PhiEdge.m
│   ├── PhiGraph.m
│   ├── PhiNode.m
│   ├── claMain.m
│   ├── in_STL_Formula
│   └── main.m
└── test
    ├── data
    ├── experiment
    └── store_data.m
```
  
