# MathFunctions


### Introduction

This README file provides a brief overview and a step-by-step guide to implement a workflow that takes two integer inputs: 'seed' and 'iters', and computes results for several mathetical functions.

### Workflow Visualization

[![](https://mermaid.ink/img/pako:eNp1k0uPgjAUhf8KuauaqEEQURaT-NYIcTLOyrDpQMVGaE0pGR31v08RxMQHTRo457unvSk9QcBDAg5sYv4bbLGQmvvlM009fbTimQhITWs0Ps7aWRsgbUoYEViSOZMkIqL2hhyiG-jSVL6jRhXlYSno4R03fs0Ncl_LgQlaUUae5Cka8vSVMUMTHEgu0tKZVM4csSz5IaIfRYJEWDElMr0jhTCrhAWKVZNPFcMKcNVyqZyopigR3wKzdMNFclvcvQcVwqgSPFQ07GWxpPuYBlhSzsq68R3THguXyKXsEwe7kl0-7n78Fi3meeWv0VNni7tZCN6j4LN8lHHFRz6gDgkRCaah-uFOOeCD3JKE-OCo1xCLnQ8-uygOZ5KvjiwAR4qM1CHbh-r8RxRHAifgbHCcKnWPGTgnOIDTMvRmq2Ublt7utQ2r0zPqcASnYzXbpt411aS3dMuyL3X441wl6E3LtG2z3enaptE1zW7nGre-mmU8Canq2isuyPWeXP4BSljrgw?type=png)](https://mermaid.live/edit#pako:eNp1k0uPgjAUhf8KuauaqEEQURaT-NYIcTLOyrDpQMVGaE0pGR31v08RxMQHTRo457unvSk9QcBDAg5sYv4bbLGQmvvlM009fbTimQhITWs0Ps7aWRsgbUoYEViSOZMkIqL2hhyiG-jSVL6jRhXlYSno4R03fs0Ncl_LgQlaUUae5Cka8vSVMUMTHEgu0tKZVM4csSz5IaIfRYJEWDElMr0jhTCrhAWKVZNPFcMKcNVyqZyopigR3wKzdMNFclvcvQcVwqgSPFQ07GWxpPuYBlhSzsq68R3THguXyKXsEwe7kl0-7n78Fi3meeWv0VNni7tZCN6j4LN8lHHFRz6gDgkRCaah-uFOOeCD3JKE-OCo1xCLnQ8-uygOZ5KvjiwAR4qM1CHbh-r8RxRHAifgbHCcKnWPGTgnOIDTMvRmq2Ublt7utQ2r0zPqcASnYzXbpt411aS3dMuyL3X441wl6E3LtG2z3enaptE1zW7nGre-mmU8Canq2isuyPWeXP4BSljrgw)


### Functions Descriptions

 #### 1. Source
              
    Acts as a propagator/ broadcaster that reads two integer inputs: 'seed' and 'iters' and relays the same to different functions.

#### 2. GenerateInteger

    Reads two integer inputs: 'seed' and 'iters'. Sets a random seed in numpy and generates a random integer in the range (0,10000). The generated random integer 'integer' and 'iters' are returned.
                      
 
#### 3. GenerateList   
        
    Reads two integer inputs: 'seed' and 'iters'. Sets a random seed in numpy and generates a random list of size in the range (0,10000). The generated random list 'list' and 'iters' are returned.
              
              
#### 4. GenerateMatrix

    Reads two integer inputs: 'seed' and 'iters'. Sets a random seed in numpy and generates a random integer in the range (0,100) for the size of the matrix. Resets the numpy random seed and a matrix of order size by size is randomly generated.The generated random matrix 'matrix', its size 'size' and 'iters' are returned.


#### 5. Sine [here](https://github.com/dream-lab/xfaas-workloads/blob/jahnavi-harini/functions/math/sine_macro/sine_macro.py)
 
    It computes the sine of the all the numbers in the range 'integer', 'iters' number of times. The same is returned as a double precision floating point number.
    
#### 6. Cosine [here](https://github.com/dream-lab/xfaas-workloads/blob/sanjjit-mohith/functions/math/fpCosineMacro/fpCosineMacro.py)

    It computes the cosine of the all the numbers in the range 'integer', 'iters' number of times. The same is returned as a double precision floating point number.
    
#### 7. Factors [here](https://github.com/dream-lab/xfaas-workloads/blob/sanjai-yash/functions/math/faasdom-python-factors/findingFactors/findFactors.py)
             
    It finds the factors of 'integer', 'iters' number of times. The same is returned as a list.

#### 8. FastFourierTransforms [here](https://github.com/dream-lab/xfaas-workloads/blob/sanjai-yash/functions/math/fft/performFft/compute.py)

    It performs FFT on a given list, 'iters' number of times. A resulting numpy array is returned.

#### 9. MatrixMultiplication [here](https://github.com/dream-lab/xfaas-workloads/blob/jahnavi-harini/functions/math/matrix_mult_low_macro/matrix_mult_low_macro.py)

    It takes two input matrices and multiplies them, 'iters' number of times. The resulting matrix is returned.

#### 10. LinPack [here](https://github.com/dream-lab/xfaas-workloads/blob/ragul-swathika/functions/math/LinPack/LinPack.py)

    It takes two input matrices and performs linpack on them. 'mflops' value is returned.

#### 11. Aggregator

    As the name suggests, it aggregates results returned by several computational functions.

    Note: NumberAggregator node aggregate integer results and ListAggregator node aggregate list results. Homogeneity of results is maintained.
    The Aggregator function aggregates all the results, expected from the workflow.

### Describing Input JSON Payload

    seed (Integer): Used to set the random seed in NumPy.
    iters (Integer): Number of times result is computed in each function.

### Describing Output JSON 

    Results: 
            Cosine (Floating Point Number): cosine of randomly generated integer.
            Sine (Floating Point Number): sine of randomly generated integer.
            Linpack (Floating Point Number): mflops from performing linpack benchmark on two randomly generated matrices.
            Factors (List): factors of randomly generated integer.
            Matrix Multiplication (2D Numpy array): resulting matrix from multiplication of randomly generated matrices.
            Fast Fourier Transform (1D Numpy array): resulting list from performing fft on randomly generated list.

### Input JSON Payload

```json
{
    "seed" : 10,
    "req": 10
}
```

### Output JSON

```json
{
    "message": "Success",
    "result": {
        "body": {
            "Cosine of 9938 degrees": -0.7986355100473039,
            "Factors of 9938": [
                1,
                2,
                4969,
                9938
            ],
            "Resulting array on performing fft": "[ 4.99079694e+03 +0.j          3.80082735e+01+33.53633634j\n -1.18088092e+01-11.56045134j ... -4.75994142e+00+38.62158706j\n -1.18088092e+01+11.56045134j  3.80082735e+01-33.53633634j]",
            "Resulting matrix from multiplication of two randomly generated matrices": "[[19.14930604 18.58565008 22.23497666 ... 21.58481502 21.87261686\n  22.27916787]\n [21.46863957 18.48090903 21.54033235 ... 21.10194909 22.17059021\n  22.55137787]\n [22.33464174 19.69769859 22.006156   ... 23.04188367 21.36568527\n  23.17874645]\n ...\n [22.81240076 19.60209105 20.95866975 ... 24.11920337 21.79761787\n  23.52962457]\n [19.4679168  18.38821174 20.77303115 ... 21.1666352  21.41010519\n  20.76355336]\n [20.41136238 16.83838638 20.93501422 ... 21.64556211 22.45365749\n  23.61403636]]",
            "Sine of 9938 degrees": -0.6018150231520335,
            "mflops on performing linpack": 1766.395036580934
        },
        "metadata": null,
        "statusCode": 200
    },
    "statusCode": 200
}
```

### Dependencies

   Python 3.10.6
   Numpy  1.24.3
   

## Authors

- [@jahnavimurali](https://www.github.com/jahnavimurali)
- [@HariniMohan2110875](https://www.github.com/HariniMohan2110875)
