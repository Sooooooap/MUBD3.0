from rdkit import DataStructs
from rdkit.Chem import AllChem as Chem
from rdkit.Chem import MACCSkeys
from rdkit.Chem.Crippen import MolLogP
from rdkit.Chem.Descriptors import MolWt
from rdkit.Chem.Lipinski import NumHAcceptors, NumHDonors, NumRotatableBonds
from rdkit.Chem.rdmolops import GetFormalCharge

import pandas as pd
import numpy as np
import re


class Cal_Max():
    """get max similarity between query decoy and all actives"""
    def __init__(self, diverse_ligands_path):
        self.diverse_ligands_path = diverse_ligands_path

    def cal_max_sim(self, mol) -> float:
        df_1  = pd.read_csv(self.diverse_ligands_path)
        s1 = list(df_1['SMILES'])
        suppl_L = []
        for i in range(0,len(s1)):
            m = Chem.MolFromSmiles(s1[i])
            suppl_L.append(m)
        
        fps = MACCSkeys.GenMACCSKeys(mol) 
        fps_L = [MACCSkeys.GenMACCSKeys(x) for x in suppl_L]

        Fps=[]                  
        for j in range(0,len(suppl_L)):         
            x=DataStructs.FingerprintSimilarity(fps,fps_L[j])  
            Fps.append(x)
        len_Fps = len(Fps)
        Sim_Max=max(Fps[i] for i in range(0,len_Fps))

        return Sim_Max  

class Cal_Min():
    """get min similarity between query decoy and all actives"""
    def __init__(self, diverse_ligands_path):
        self.diverse_ligands_path = diverse_ligands_path

    def cal_min_sim(self, mol) -> float:
        df_1  = pd.read_csv(self.diverse_ligands_path)
        s1 = list(df_1['SMILES'])
        suppl_L = []
        for i in range(0,len(s1)):
            m = Chem.MolFromSmiles(s1[i])
            suppl_L.append(m)
        
        fps = MACCSkeys.GenMACCSKeys(mol) 
        fps_L = [MACCSkeys.GenMACCSKeys(x) for x in suppl_L]

        Fps=[]                  
        for j in range(0,len(suppl_L)):         
            x=DataStructs.FingerprintSimilarity(fps,fps_L[j])  
            Fps.append(x)
        len_Fps = len(Fps)
        Sim_Min=min(Fps[i] for i in range(0,len_Fps))

        return Sim_Min

class Cal_Simp():
    """ get simp """
    def __init__(self, diverse_ligands_ps_path, diverse_ligands_ps_max_min_path, active_index):
        self.diverse_ligands_ps_path = diverse_ligands_ps_path
        self.diverse_ligands_ps_max_min_path = diverse_ligands_ps_max_min_path
        self.query_idx = [int(s) for s in re.findall(r'\d+', active_index)][0]

    def Normalization(self, x, Max, Min):
        if  Max == Min :
            x = 1
            return x
        else:
            x = float(x-Min) / float(Max-Min)    
            return x
    
    def Middle(self, PIT, PIR):
        x = PIT - PIR
        y = np.square(x) 
        return y

    def simp_tr(self, mol) -> float:
        df_PS_maxmin = pd.read_csv(self.diverse_ligands_ps_max_min_path, index_col=0)
        MW_Max = df_PS_maxmin.iloc[0,0]
        MW_Min = df_PS_maxmin.iloc[1,0]
        NR_Max = df_PS_maxmin.iloc[2,0]
        NR_Min = df_PS_maxmin.iloc[3,0]
        HD_Max = df_PS_maxmin.iloc[4,0]   
        HD_Min = df_PS_maxmin.iloc[5,0]
        HA_Max = df_PS_maxmin.iloc[6,0]
        HA_Min = df_PS_maxmin.iloc[7,0]
        FC_Max = df_PS_maxmin.iloc[8,0]
        FC_Min = df_PS_maxmin.iloc[9,0]
        LogP_Max = df_PS_maxmin.iloc[10,0]
        LogP_Min = df_PS_maxmin.iloc[11,0]

        df1 = pd.read_csv(self.diverse_ligands_ps_path)
        MW_t = df1['MW_MCS']
        NR_t = df1['NR_MCS']
        HD_t = df1['HD_MCS']
        HA_t = df1['HA_MCS']
        FC_t = df1['FC_MCS']
        LogP_t = df1['LogP_MCS']

        simp1=self.Middle(MW_t[self.query_idx],self.Normalization(MolWt(mol), MW_Max, MW_Min))
        simp2=self.Middle(NR_t[self.query_idx],self.Normalization(NumRotatableBonds(mol), NR_Max,NR_Min))
        simp3=self.Middle(HD_t[self.query_idx],self.Normalization(NumHDonors(mol), HD_Max, HD_Min))
        simp4=self.Middle(HA_t[self.query_idx],self.Normalization(NumHAcceptors(mol), HA_Max, HA_Min))
        simp5=self.Middle(FC_t[self.query_idx],self.Normalization(GetFormalCharge(mol), FC_Max, FC_Min))
        simp6=self.Middle(LogP_t[self.query_idx],self.Normalization(MolLogP(mol), LogP_Max, LogP_Min))
        simp = 1-np.sqrt((simp1+simp2+simp3+simp4+simp5+simp6)/6)       
        
        return simp

class Cal_Simsdiff():
    """get simsdiff"""
    def __init__(self, diverse_ligands_path, active_index):
        self.diverse_ligands_path = diverse_ligands_path
        self.query_idx = [int(s) for s in re.findall(r'\d+', active_index)][0]

    def simsdiff_qr(self, mol) -> float:
        df_DL = pd.read_csv(self.diverse_ligands_path)
        s_list = list(df_DL['SMILES'])
        suppl2 = [Chem.MolFromSmiles(smi) for smi in s_list]
        fps2 = [MACCSkeys.GenMACCSKeys(y) for y in suppl2]

        sum = 0
        for j in range(0, len(suppl2)):
            if self.query_idx != j:
                sim1 = DataStructs.FingerprintSimilarity(MACCSkeys.GenMACCSKeys(mol), fps2[j])
                sim2 = DataStructs.FingerprintSimilarity(fps2[self.query_idx], fps2[j])
                sum += abs(sim1 - sim2)
        sims_mean = sum / (len(suppl2) - 1)
        return sims_mean