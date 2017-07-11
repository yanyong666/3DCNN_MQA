import os
import sys
import subprocess
import commands
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.PDB import *
from tqdm import tqdm
p = PDBParser(QUIET=True)
import argparse


sys.path.append(os.path.join(os.path.dirname(__file__),'../DatasetsProperties/'))
sys.path.append(os.path.join(os.path.dirname(__file__),'..'))
from plotLengthDistributions import read_dataset_targets, read_sequences_data
from plotTrainingProcess import read_dataset_description, read_epoch_output, plotFunnels

ProQ3Path = '/home/lupoglaz/ProteinQA/proq3'

def prepare_dataset(dataset_name, output_dir, target_beg = None, target_end = None, subset = None):
	target_seq = read_sequences_data('../DatasetsProperties/data')
	dataset_path = '/scratch/ukg-030-aa/lupoglaz/%s/Description'%dataset_name
	test_dataset_targets = read_dataset_targets(dataset_path, 'datasetDescription.dat')
	proteins, decoys = read_dataset_description(dataset_path, 'datasetDescription.dat', decoy_ranging='gdt-ts')
	if not os.path.exists(output_dir):
		os.mkdir(output_dir)
	results_dir = os.path.join(output_dir,dataset_name)
	if not os.path.exists(results_dir):
		os.mkdir(results_dir)

	if not (subset is None):
		proteins = subset
	
	for n,protein in enumerate(proteins):
		if (n >= target_beg) and (n<target_end):
			print protein
			try:
				os.mkdir(os.path.join(results_dir, protein))
			except:
				pass
			decoys_output_filename = os.path.join(results_dir, protein, 'decoys.txt')
			fasta_output_filename = os.path.join(results_dir, protein, 'seq.fasta')
			with open(decoys_output_filename,'w') as fout:
				for decoy in decoys[protein]:
					fout.write('%s\n'%(decoy[0]))
			with open(fasta_output_filename, 'w') as fout:
				SeqIO.write(SeqRecord(target_seq[protein],id=protein), fout, "fasta")

def score_decoys(decoys_list_path, sequence_path, output_path):
	os.chdir(ProQ3Path)
	os.system('bash run_proq3.sh -l %s -fasta %s -deep yes -outpath %s'%(decoys_list_path, sequence_path, output_path))
	os.chdir(os.path.realpath(__file__)[:os.path.realpath(__file__).rfind('/')])

def score_decoys_preprofiled(decoys_list_path, profile_path, output_path ):
	os.chdir(ProQ3Path)
	os.system('bash run_proq3.sh -l %s -profile %s -deep no -outpath %s'%(decoys_list_path, profile_path, output_path))
	os.chdir(os.path.realpath(__file__)[:os.path.realpath(__file__).rfind('/')])

def score_dataset(dataset_dir, profiles_dataset_dir=None, target_beg = None, target_end = None):
	for n,target in enumerate(os.listdir(dataset_dir)):
		if (n >= target_beg) and (n<target_end):
			target_dir = os.path.join(dataset_dir, target)
			decoys_list_path = os.path.join(target_dir, 'decoys.txt')
			sequence_path = os.path.join(target_dir, 'seq.fasta')
			if profiles_dataset_dir is None:
				score_decoys(decoys_list_path, sequence_path, target_dir)
			else:
				profile_path = os.path.join(profiles_dataset_dir, target, 'seq.fasta')
				score_decoys_preprofiled(decoys_list_path, profile_path, target_dir)

def get_scores(dataset_name, proq3_output_dir):
	proteins, decoys = read_dataset_description('/scratch/ukg-030-aa/lupoglaz/%s/Description'%dataset_name,
												'datasetDescription.dat', decoy_ranging='gdt-ts')
	scores_dict = {}
	for protein in proteins:
		scores_dict[protein] = []
		prot_output_dir = os.path.join(proq3_output_dir, protein)
		for decoy_path, gdt in decoys[protein]:
			decoy_name = decoy_path[decoy_path.rfind('/')+1:]
			output_file = os.path.join(prot_output_dir, decoy_name+'.pdb.proq3.global')
			
			if not os.path.exists(output_file):
				print 'No output:', output_file
				scores_dict[protein].append( (decoy_path, None) )
				continue

			with open(output_file, 'r') as fin:
				_ = fin.readline()
				scores = fin.readline().split()
				float_scores = [float(x) for x in scores]
				scores_dict[protein].append((decoy_path, float_scores))
				# print float_scores
	
	return scores_dict

def write_scores(proq3_output_dir, scores, score_num = 3):
	with open(os.path.join(proq3_output_dir, 'epoch_0.dat'), 'w') as fout:
		fout.write("Decoys scores:\n")
		for protein in scores.keys():
			for decoy_path, score in scores[protein]:
				# print score
				fout.write("%s\t%s\t%f\n"%(protein, decoy_path, score[score_num]))

		fout.write("Loss function values:\n")
		fout.write("Decoys activations:\n")

if __name__=='__main__':
	parser = argparse.ArgumentParser(prog='ProQ3Script', 
									formatter_class=argparse.RawDescriptionHelpFormatter,
									description="""\
									Runs ProQ3 for targets in a dataset.
									""")
	parser.add_argument('--dataset_name', metavar='dataset_name', type=str, 
				   help='Dataset name', default='CASP11Stage1_SCWRL')
	parser.add_argument('--start_num', metavar='start_num', type=int, 
				   help='Starting number of target', default=0)
	parser.add_argument('--end_num', metavar='end_num', type=int, 
				   help='Ending number of target', default=1)

	stage1_unprocessed = ['T0781', 'T0824', 'T0843', 'T0817', 'T0774', 'T0790', 'T0811', 'T0772', 'T0820', 'T0776', 'T0814', 'T0759', 'T0838', 'T0801', 'T0767', 'T0807', 'T0857', 'T0777', 'T0766', 'T0816', 'T0785', 'T0829', 'T0815', 'T0773', 'T0789', 'T0855', 'T0848', 'T0836', 'T0853', 'T0821', 'T0827', 'T0837', 'T0831', 'T0819', 'T0760', 'T0797', 'T0810', 'T0822', 'T0792', 'T0832']

	stage2_unprocessed = ['T0824', 'T0784', 'T0786', 'T0782', 'T0817', 'T0774', 'T0805', 'T0772', 'T0764', 'T0820', 'T0776', 'T0814', 'T0780', 'T0759', 'T0838', 'T0818', 'T0801', 'T0767', 'T0807', 'T0849', 'T0762', 'T0857', 'T0777', 'T0768', 'T0852', 'T0854', 'T0800', 'T0766', 'T0808', 'T0816', 'T0785', 'T0794', 'T0796', 'T0856', 'T0773', 'T0825', 'T0789', 'T0855', 'T0830', 'T0803', 'T0771', 'T0836', 'T0845', 'T0853', 'T0821', 'T0788', 'T0783', 'T0841', 'T0837', 'T0831', 'T0819', 'T0760', 'T0797', 'T0835', 'T0810', 'T0822', 'T0832']
		
	args = parser.parse_args()
	prepare_dataset('CASP11Stage1_SCWRL', '/scratch/ukg-030-aa/lupoglaz/models/ProQ3', target_beg=args.start_num, target_end=args.end_num, subset=stage1_unprocessed) 
	score_dataset('/scratch/ukg-030-aa/lupoglaz/models/ProQ3/CASP11Stage1_SCWRL', target_beg=args.start_num, target_end=args.end_num)
	