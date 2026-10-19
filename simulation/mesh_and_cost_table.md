| Curve | Solver and mesh setting | Elements | Unknowns | Effective element size (relative to COMSOL index 5) | Sweep points | Run time | Peak memory |
|---|---|---|---|---|---|---|---|
| COMSOL index 9 | COMSOL 6.1, Physics-Controlled Mesh, index 9 | 163,205 | not recorded | 1.30 | 13 | 536 s for the sweep | not logged |
| COMSOL index 8 | COMSOL 6.1, Physics-Controlled Mesh, index 8 | 180,447 | not recorded | 1.26 | 13 | 533 s for the sweep | not logged |
| COMSOL index 7 | COMSOL 6.1, Physics-Controlled Mesh, index 7 | 221,979 | not recorded | 1.18 | 13 | 585 s for the sweep | not logged |
| COMSOL index 6 | COMSOL 6.1, Physics-Controlled Mesh, index 6 | 267,299 | not recorded | 1.11 | 13 | 629 s for the sweep | not logged |
| COMSOL index 5 | COMSOL 6.1, Physics-Controlled Mesh, index 5 | 361,970 | not recorded | 1.00 | 13 | 890 s for the sweep | not logged |
| COMSOL index 7, copper loss and real vias | same, copper as thickness-aware boundary, 90 via cylinders | 232,555 | not recorded | 1.16 | 13 | 593 s for the sweep | not logged |
| Palace 400 µm | Palace 0.18.1, order 2, refined cell size 400 µm | 153,782 | 1,101,132 | n/a | 13 | 98 min for the sweep (6 min per point), 3 MPI ranks | 3.9 GB in the largest rank; total not logged |
| Palace 300 µm | Palace 0.18.1, order 2, refined cell size 300 µm, GMRES restart 50 | 171,567 | 1,228,090 | 0.96 (relative to Palace 400 µm) | 4 | about 11.5 min per point, one point per process | about 9.6 GB used by WSL, up to 10.9 GB at the end of a solve |

Hardware: laptop with a Ryzen 5 7530U (6 cores) and 13.9 GB RAM; Palace ran in WSL with an 11 GB limit and 4 GB swap. COMSOL 6.1 used 6 cores. Palace's linear solver: GMRES, tolerance 1e-6, p-multigrid with a complex coarse solve (SuperLU). COMSOL's: GMRES with a geometric multigrid preconditioner (default). The Palace element counts are those of the solver, which adds interface elements to the 152,587 and 170,117 tetrahedra in the mesh files. Effective element size is (elements)^(-1/3) relative to the reference mesh; the cell-size setting of Palace changes it by only about 3% per step because the thin layers and vias limit the mesh.
