# Extracts data from the database
# Performs an obscene amount of joins for you - dont try to do it manually
# example call: python dbToFile.py -r 2015_08_10_19_34_7597 -b 2_3 -d /tmp

import os
import MySQLdb
from optparse import OptionParser
import time
import subprocess

db = MySQLdb.connect(user = "root", passwd = 'TCADgBq7ShmpYfN3', db = 'assay_calib_sims', 
        host = 'localhost')
con = db.cursor()

# Inputs
createIndex = True
# Command Parsing {{{
parser = OptionParser()
parser.add_option("-r", "--run_id", dest="run_id",
        help="run_id as generated by simulator.second.py")
parser.add_option("-b", "--bio_prot",
                        dest="bio_prot",
                        help="what biology_protocol pairs to use: comma seperated list (e.g. 1_0,2_2). This is the last part of the table names in MySQL")
parser.add_option("-d", "--directory", dest="scriptDir",
        default = '/home/phillipl/projects/assay_calib_sims/data/',
        help="directory into which the data will be placed.")

(options, args) = parser.parse_args()

print options
#}}}

runName     = options.run_id
biol_prots  = [options.bio_prot]
scriptDir   = options.scriptDir

# Permanent Data
tabs = ['prottab', 'cohorttab', 'subtab', 'visittab']
id_cols = ['biol_id', 'prot_id', 'cohort_id', 'sub_id', 'visit_id']

try:
    if createIndex:
        for fp in biol_prots:
            con.execute("CREATE INDEX index1 ON run_%s_prottab_%s (biol_id, prot_id)" %(runName, fp,))
            con.execute("CREATE INDEX index1 ON run_%s_cohorttab_%s (biol_id, prot_id, cohort_id)" %(runName, fp,))
            con.execute("CREATE INDEX index1 ON run_%s_subtab_%s (biol_id, prot_id, cohort_id, sub_id)" %(runName, fp,))
            con.execute("CREATE INDEX index1 ON run_%s_visittab_%s (biol_id, prot_id, cohort_id, sub_id)" %(runName, fp,))
            db.commit()
except:
    print "Indexes already existed"

for fp in biol_prots:
    print fp
    cols = []
    shrt_cols = []
    for tab in tabs:
        full_tab_name = "run_%s_%s_%s" %(runName, tab, fp, )
        con.execute("describe %s"%full_tab_name )
        the_cols = []
        the_shrt_cols = []
        for stuff in [i[0] for i in con.fetchall()]:
            if stuff.count("_id") == 0:
                the_cols.append(full_tab_name+"."+stuff)
                the_shrt_cols.append(stuff)
        cols += the_cols
        shrt_cols += the_shrt_cols

    qstring='''
    SELECT run_%s_%s_%s.biol_id, 
        run_%s_%s_%s.prot_id, 
        run_%s_%s_%s.cohort_id, 
        run_%s_%s_%s.sub_id, 
        run_%s_%s_%s.visit_id, 
        %s 
    FROM
        run_%s_%s_%s,
        run_%s_%s_%s,
        run_%s_%s_%s,
        run_%s_%s_%s
    WHERE
    run_%s_%s_%s.biol_id = run_%s_%s_%s.biol_id
    AND run_%s_%s_%s.prot_id = run_%s_%s_%s.prot_id
    
    AND run_%s_%s_%s.biol_id = run_%s_%s_%s.biol_id
    AND run_%s_%s_%s.prot_id = run_%s_%s_%s.prot_id
    AND run_%s_%s_%s.cohort_id = run_%s_%s_%s.cohort_id

    AND run_%s_%s_%s.biol_id = run_%s_%s_%s.biol_id
    AND run_%s_%s_%s.prot_id = run_%s_%s_%s.prot_id
    AND run_%s_%s_%s.cohort_id = run_%s_%s_%s.cohort_id
    AND run_%s_%s_%s.sub_id = run_%s_%s_%s.sub_id
    '''% (runName, tabs[3], fp,
        runName, tabs[3], fp,
        runName, tabs[3], fp,
        runName, tabs[3], fp,
        runName, tabs[3], fp,
        ", ".join(cols), 
        runName, tabs[0], fp, # tablist 1
        runName, tabs[1], fp, # tablist 2
        runName, tabs[2], fp, # tablist 3
        runName, tabs[3], fp, # tablist 4
        runName, tabs[0], fp, # join 1 - 1 - 1
        runName, tabs[1], fp, # join 1 - 1 - 2
        runName, tabs[0], fp, # join 1 - 2 - 1
        runName, tabs[1], fp, # join 1 - 2 - 2
        runName, tabs[1], fp, # join 2 - 1 - 1
        runName, tabs[2], fp, # join 2 - 1 - 2
        runName, tabs[1], fp, # join 2 - 2 - 1
        runName, tabs[2], fp, # join 2 - 2 - 2
        runName, tabs[1], fp, # join 2 - 3 - 1
        runName, tabs[2], fp, # join 2 - 3 - 2
        runName, tabs[2], fp, # join 3 - 1 - 1
        runName, tabs[3], fp, # join 3 - 1 - 2
        runName, tabs[2], fp, # join 3 - 2 - 1
        runName, tabs[3], fp, # join 3 - 2 - 2
        runName, tabs[2], fp, # join 3 - 3 - 1
        runName, tabs[3], fp, # join 3 - 3 - 2
        runName, tabs[2], fp, # join 3 - 4 - 1
        runName, tabs[3], fp # join 3 - 4 - 2
        )
    print qstring
    cqstring = "CREATE TABLE IF NOT EXISTS run_%s_train_%s " %(runName, fp, ) + qstring
    con.execute(cqstring)
    db.commit()
    print id_cols+shrt_cols
    if not os.path.isdir(os.path.join(scriptDir, '%s' %runName )):
        print(os.path.join(scriptDir, '%s' %runName ))
        os.mkdir(os.path.join(scriptDir, '%s' %runName ))#'data/%s' %runName)

    indx_string = "ALTER TABLE run_%s_train_%s ADD INDEX `indx1` (`cohort_id` ASC, `sub_id` ASC, `visit_id` ASC)" %(runName, fp, )
    try:
        con.execute(indx_string)
        db.commit()
    except:
        print "index already existed"

    f = open(os.path.join(scriptDir, '%s/train%s.txt' %(runName, fp,)) ,'w')
    f.writelines("|".join([str(i) for i in id_cols+shrt_cols])+'\n')
    g = open(os.path.join(scriptDir, '%s/test%s.txt' %(runName, fp,)) ,'w')
    g.writelines("|".join(["biol_id", "prot_id", "cohort_id", "sub_id", "visit_id", "visit_date", "bmv"])+'\n')
    g.close()

    # If the dataset is smallish, write to file
    con.execute("select count(*) from run_%s_train_%s " %(runName, fp, ))
    dataSetSize = con.fetchall()[0][0]
    print dataSetSize
    if dataSetSize < 10:
        con.execute(qstring)
        data=con.fetchall() # gonna run outta ram here <<<<---- :p
        for i in data[:5]:
            print i
        for i in data:
            f.writelines("|".join([str(j) for j in i])+'\n')
        f.close()
    else:
        f.close()
        print "file too large - dont pull the data into ram in python instead push it directly from mysql into a file"
        print "train data set"
        dump_string = "SELECT * from run_%s_train_%s into outfile '/tmp/train%s%s.txt.noheader' fields terminated by '|'" %(runName, fp, runName, fp)
        print dump_string
        con.execute(dump_string)
        print "sleeping - wait a little to prevent the next step from starting before the file write is completed"
        time.sleep(10)
        command = "cat /tmp/train%s%s.txt.noheader >> %s/%s/train%s.txt"%(runName, fp, scriptDir, runName, fp)
        print command
        subprocess.call(command, shell = True)

        print "test data set"
        dump_string = "SELECT * from run_%s_visittab_%s into outfile '/tmp/test%s%s.txt.noheader' fields terminated by '|'" %(runName, fp, runName, fp)
        print dump_string
        con.execute(dump_string)
        print "sleeping - wait a little to prevent the next step from starting before the file write is completed"
        time.sleep(10)
        command = "cat /tmp/test%s%s.txt.noheader >> %s/%s/test%s.txt"%(runName, fp, scriptDir, runName, fp)
        print command
        subprocess.call(command, shell = True)

    db.close()
