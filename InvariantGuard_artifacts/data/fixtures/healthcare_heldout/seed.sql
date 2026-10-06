INSERT INTO departments VALUES (1,'Cardiology'),(2,'Oncology'),(3,'Pharmacy');
INSERT INTO clinicians VALUES (10,1,NULL,'NPI-0010'),(11,1,10,'NPI-0011'),
                              (12,2,NULL,'NPI-0012'),(13,2,12,'NPI-0013'),
                              (14,3,NULL,'NPI-0014');
INSERT INTO patients VALUES (100,'MRN-100','Alpha',TRUE),(101,'MRN-101','Beta',TRUE),
                            (102,'MRN-102','Gamma',TRUE),(103,'MRN-103','Delta',FALSE);
INSERT INTO encounters VALUES (200,100,'open'),(201,100,'discharged'),
                              (202,101,'open'),(203,102,'open'),(204,103,'cancelled');
INSERT INTO encounter_clinicians VALUES (200,10,'attending'),(200,11,'nurse'),
                                        (201,10,'attending'),(202,12,'attending'),
                                        (202,13,'consulting'),(203,12,'attending');
INSERT INTO orders VALUES (300,200,50,10),(301,200,25,11),(302,202,100,12),
                          (303,203,10,12),(304,201,75,10);
INSERT INTO administrations VALUES (400,300,TRUE),(401,300,FALSE),(402,302,TRUE),
                                   (403,303,FALSE),(404,304,TRUE);
