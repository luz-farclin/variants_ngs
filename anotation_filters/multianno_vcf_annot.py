import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input')
parser.add_argument('-v', '--vcf')
parser.add_argument('-o', '--output')
args = parser.parse_args()

file_vcf = args.vcf
file_annot = args.input
file_out = args.output

# file_vcf = "17NR2116_1_sorted.vcf"
# file_annot = "17NR2116_1_sorted.vcf.hg38_multianno.csv"
# file_out = "patata.txt"

fichero_vcf = open(file_vcf,"r")
fichero_annot = open(file_annot, "r")
fichero_out = open(file_out,"w")

#Creamos un diccionario de genotipos

genot = {}

for linea in fichero_vcf:
    linea = linea.strip("\n")
    linea = linea.split("\t")
    if linea > 1:
        tag = "".join(linea[0:5])
        genot[tag] = linea[5] + "_" + linea[6]

#Incorporamos la info al multiannot

for linea in fichero_annot:
    linea = linea.strip("\n")
    linea = linea.split(",")
    if linea > 1:
        tag = "".join(linea[0:5])
        if tag in genot:
            geno = genot[tag]
            geno = geno.split("_")
        else:
            geno = ["",""]
        linea_out = linea[0:5]
        linea_out.extend(geno)
        linea_out.extend(linea[5:])
        fichero_out.write(",".join(linea_out) + "\n")


