# solvis

a demo to try some techniques for analysis of opensha modular solution files.

 - opensha modular documentation
 - pandas, geopanda references

## goals

From a typical modular opensha Inversion Solution archive, we want to produce views that allow deep exploration 
of the solution and rupture set characteristics. Features:

 - [ ] user can choose from regions already defined in the solution
 - user can select ruptures matching 
    - [ ] parent fault
    - [ ] named fault (fault system)
    - [ ] constraint region (from TargetMFDs)
 - [ ] user can create new region polygons 
 - [ ] user can compare selections (e.g. Wellington East vs Wellington CBD vs Hutt Valley) 
 - for a given query result show me dimensions...
    - mag, length, area, rate, section count, parent fault count, jump-length, jump angles, slip (various), partication, nucleation 
    - filter, group on any of the dimensions


## From here the user can answer questions like ....

 - create a MFD histogram in 0.01 bins from 7.0 to 7.30 (3O bins) for the WHV fault system
 - find all ruptures between 7.75 and 8.25, involving the TVZ, grouped by the number of parent faults, ordered by rupture-length (reverse)
 - given a user-defined-function udfRuptureComplexity(rupture) rank ruptures in Region X by complexity, then by magnitude
 

