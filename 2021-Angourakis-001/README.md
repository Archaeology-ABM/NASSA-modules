# Random walk in 2D space based on agent angle orientation
*by Andreas Angourakis* (NASSA submission :rocket:)

An implementation of random walk in Python, which defines an agent class `Walker` capable of several movement algorithms based on angle and movement step distance in a continuous 2D space.

- class `Walker`, which includes methods for random walk (could be extended with other walking methods):
    - `MoveRandom(angleLeftMax, angleRightMax, moveDistanceMin, moveDistanceMax, worldDimensions)`: 2D random walk with parameters for direction and distance variation and limited to given world dimensions. Uses uniform distributions for random values. Sets Walker instance new position and returns new x, y, and direction in degrees.
    - `MoveRandomFree(angleLeftMax, angleRightMax, moveDistanceMin, moveDistanceMax)`: 2D random walk with parameters for direction and distance variation. Uses uniform distributions for random values. Returns new x, y, and direction in degrees.
    - `GetRandomRotation(currentDirection, angleLeftMax, angleRightMax)`: Rotate initial direction randomly within the range `(currentDirection - angleLeftMax, currentDirection + angleRightMax)`. Uses uniform distributions for random values. Returns new direction in degrees.
    - `IsOutsideWorld(self, x, y, worldDimensions)`: Checks if the coordinates are outside the world dimensions. Returns Boolean (true/false). 
    - Static methods for testing instance methods. Testing is limited here to printing result in a more readable manner. 

![variables and parametres](https://github.com/Archaeology-ABM/test-modules/blob/main/RandomWalk/PythonVersion_01/documentation/variablesAndParametres.png)

- `demonstration.ipynb`: Jupyter Notebook that sets up a workflow for executing several random walks and plotting them. It also includes a demonstration of the test methods.
