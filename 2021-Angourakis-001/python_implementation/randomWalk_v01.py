############################
# Random walk module - version 01
# by Andreas Angourakis (18/03/2021)
# test script for the Network for Agent-based modelling of Socio-ecological systems in Archaeology (NASA)

import math
import random

class Walker:
    '''
    Walker is an agent class that includes methods for random walking 
    (could be extended with other walking methods):
    
    positionX, positionY: agent's position in 2D coordinates 
    direction: agent's angular direction in degrees

    Methods:

    MoveRandom(angleLeftMax, angleRightMax, moveDistanceMin, moveDistanceMax, worldDimensions)
    
    MoveRandomFree(angleLeftMax, angleRightMax, moveDistanceMin, moveDistanceMax)
    
    GetRandomRotation(currentDirection, angleLeftMax, angleRightMax)

    IsOutsideWorld(self, x, y, worldDimensions)
    
    Static methods for testing instance methods. 
    Testing is limited here to printing result in a more readable manner.
    '''
    def __init__(self, x, y, direction):
        self.positionX = x
        self.positionY = y
        self.direction = 0.0
    
    def MoveRandom(self,
                   angleLeftMax = 180, 
                   angleRightMax = 180, 
                   moveDistanceMin = 1.0, 
                   moveDistanceMax = 1.0,
                   worldDimensions = {'x':(-50,50), 'y':(-50,50)}):
        '''
        2D random walk with parameters for direction and distance variation 
        and limited to given world dimensions. Uses uniform distributions for random values. 
        Sets Walker instance new position and returns new x, y, and direction in degrees.
        '''
        ### get new position
        x,y,newDirection = self.MoveRandomFree(angleLeftMax, angleRightMax,
                             moveDistanceMin, moveDistanceMax)
        ### assure that new position is within world dimensions
        while self.IsOutsideWorld(x, y, worldDimensions):
            x,y,newDirection = self.MoveRandomFree(angleLeftMax, angleRightMax,
                                 moveDistanceMin, moveDistanceMax)
        ### set new position
        self.positionX = x
        self.positionY = y
        self.direction = newDirection
        ### return position coordinates and direction (display or testing purposes)
        return x,y,newDirection

    def MoveRandomFree(self,
                       angleLeftMax = 180, 
                       angleRightMax = 180, 
                       moveDistanceMin = 1.0, 
                       moveDistanceMax = 1.0):
        '''
        2D random walk with parameters for direction and distance variation. 
        Uses uniform distributions for random values. Returns new x, y, and direction in degrees.
        '''
        ### set new random direction
        newDirection = self.GetRandomRotation(self.direction, angleLeftMax, angleRightMax)
        ### convert angle to radians
        directionInRadians = newDirection * math.pi / 180
        ### get movement distance
        moveDist = moveDistanceMin + (moveDistanceMax - moveDistanceMin) * random.uniform(0,1)
        ### get new position
        x = math.cos(directionInRadians) * moveDist
        y = math.sin(directionInRadians) * moveDist
        ### return position coordinates and direction
        return x,y,newDirection
    
    def GetRandomRotation(self,
                          currentDirection,
                          angleLeftMax = 180, 
                          angleRightMax = 180):
        '''
        Rotate initial direction randomly within the range 
        (currentDirection - angleLeftMax, currentDirection + angleRightMax). 
        Uses uniform distributions for random values. Returns new direction in degrees.
        '''
        ### get new random direction from previous direction 
        ### within the range -angleLeftMax, +angleRightMax
        newDirection = random.uniform(currentDirection - angleLeftMax, 
                                      currentDirection + angleRightMax)
        ### convert negative angle to positive
        if newDirection < 0.0:
           newDirection += 360
        return newDirection

    def IsOutsideWorld(self, x, y, worldDimensions):
        return x < worldDimensions['x'][0] or x > worldDimensions['x'][1] or y < worldDimensions['y'][0] or y > worldDimensions['y'][1]

    ###################################################################
    ####### tests #####################################################
    ###################################################################
    
    def Test_IsOutsideWorld(x, y, worldDimensions):
        '''
        Checks if the coordinates are outside the world dimensions. Returns Boolean (true/false). 
        '''
        ### create class instance
        randomWalker = Walker(x, y, 0.0)

        return ("IsOutsideWorld("
               + "x = " + str(x) 
               + ", y = " + str(y) 
               + ", worldDimensions = " + str(worldDimensions)
               + ") -> "
               + str(randomWalker.IsOutsideWorld(x, y, worldDimensions)))
    
    Test_IsOutsideWorld = staticmethod(Test_IsOutsideWorld)

    def Test_GetRandomRotation(currentDirection, angleLeftMax = 180, angleRightMax = 180):
        '''
        Checks if GetRandomRotation() returns an angle within the given specifications. Returns message ending with Boolean (true/false). 
        '''
        ### create class instance
        randomWalker = Walker(0.0, 0.0, currentDirection)

        ### find left and right angle limits
        rightLimit = (currentDirection + angleRightMax)
        if rightLimit > 360: rightLimit = rightLimit - 360
        leftLimit = (currentDirection - angleLeftMax)
        if leftLimit < 0: leftLimit = 360 + leftLimit
        
        ### get new direction
        newDirection = randomWalker.GetRandomRotation(currentDirection, angleLeftMax, angleRightMax)
        
        ### test
        passTest = False
        ### case 1: the whole range is greater than 0 and lower than 360
        if (newDirection >= leftLimit) & (newDirection <= rightLimit):
            passTest = True
        ### other cases, the range overlaps with the limit 360-0
        ### case 2: newDirection falls on the left of 0-360
        elif (newDirection >= leftLimit) & (newDirection <= 360 + rightLimit):
            passTest = True
        ### case 3: newDirection falls on the right of 0-360
        elif (newDirection >= leftLimit - 360) & (newDirection <= rightLimit):
            passTest = True
        ### case 4: newDirection equals 0-360
        elif ((newDirection == 0) | (newDirection == 360)) & ((leftLimit <= 360) & (rightLimit >= 0)):
            passTest = True

        return ("GetRandomRotation("
                + "currentDirection = " + str(currentDirection)
                + ", angleLeftMax = " + str(angleLeftMax)
                + ", angleRightMax = " + str(angleRightMax)
                + ") -> newDirection = "
                + str(newDirection) + " | pass test = " + str(passTest))
    
    Test_GetRandomRotation = staticmethod(Test_GetRandomRotation)

    def Test_MoveRandomFree(x, y, currentDirection,
                            angleLeftMax = 180, 
                            angleRightMax = 180, 
                            moveDistanceMin = 1.0, 
                            moveDistanceMax = 1.0):
        '''
        Checks if MoveRandomFree() returns a position and direction within the given specifications. Returns message. 
        '''
        ### create class instance
        randomWalker = Walker(x, y, currentDirection)
        
        return ("Walker("
                + "x = " + str(x)
                + ", y = " + str(y)
                + ", currentDirection = " + str(currentDirection) + ") -> " 
                + "MoveRandomFree("
                + "angleLeftMax = " + str(angleLeftMax)
                + ", angleRightMax = " + str(angleRightMax)
                + ", moveDistanceMin = " + str(moveDistanceMin)
                + ", moveDistanceMax = " + str(moveDistanceMax)
                + ") -> (x,y,newDirection) = "
                + str(randomWalker.MoveRandomFree(angleLeftMax, angleRightMax, moveDistanceMin, moveDistanceMax)))

    Test_MoveRandomFree = staticmethod(Test_MoveRandomFree)

    def Test_MoveRandom(x, y, currentDirection,
                        angleLeftMax = 180, 
                        angleRightMax = 180, 
                        moveDistanceMin = 1.0, 
                        moveDistanceMax = 1.0,
                        worldDimensions = {'x':(-50,50), 'y':(-50,50)}):
        '''
        Checks if MoveRandom() returns a position and direction within the given specifications. Returns message. 
        '''
        ### create class instance
        randomWalker = Walker(x, y, currentDirection)
        
        return ("Walker("
                + "x = " + str(x)
                + ", y = " + str(y)
                + ", currentDirection = " + str(currentDirection) + ") -> " 
                + "MoveRandom("
                + "angleLeftMax = " + str(angleLeftMax)
                + ", angleRightMax = " + str(angleRightMax)
                + ", moveDistanceMin = " + str(moveDistanceMin)
                + ", moveDistanceMax = " + str(moveDistanceMax)
                + ", worldDimensions = " + str(worldDimensions)
                + ") returns (x,y,newDirection) = "
                + str(randomWalker.MoveRandom(angleLeftMax, angleRightMax, moveDistanceMin, moveDistanceMax, worldDimensions)))

    Test_MoveRandom = staticmethod(Test_MoveRandom)
        