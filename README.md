# UE-Satellite-Aligning-tools

## Model
This tool uses a 2D - 2D transformation model:
$$
\begin{bmatrix}
    s_1 & 0 \\
    0 & s_2
\end{bmatrix}
\begin{bmatrix}
    r_{00} & r_{01} \\
    r_{10} & r_{11}
\end{bmatrix}
\begin{bmatrix}
    x \\ y
\end{bmatrix} + 
\begin{bmatrix}
    t_0 \\ t_1
\end{bmatrix}= 
\begin{bmatrix}
    B \\ L
\end{bmatrix}
$$
and solve for the parameters with least squares via SVD.

## Build
### Environment
```
conda create -n aligning python=3.11
conda activate aligning
```
### Dependecies
```
pip install -r requirements.txt
pip install Colosseum/PythonClient --no-build-isolation
```