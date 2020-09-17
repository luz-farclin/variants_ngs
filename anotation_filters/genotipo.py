import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input')
parser.add_argument('-o', '--output')
args = parser.parse_args()

file = args.input
file_out = args.output

#file = "17NR2116_1_sorted.vcf_awk.vcf"
#file_out = "patata.txt"

fichero = open(file,"r")
fichero_out = open(file_out,"w")



j = 0
for linea in fichero:
    j += 1
    linea = linea.strip("\n")
    linea = linea.split("\t")
    if len(linea) > 5:
        ref = linea[3]
        alt = linea[4]
        gt = linea[5]
        # Generamos la lista de alelos
        alelos = []
        alelos.append(ref)
        alt = alt.split(",")
        for i in alt:
            alelos.append(i)
        # Separar columna genotipos
        gt = gt.split(":")
        patata = gt[0].split("/")
        # Definir HOM o HET
        geno = ""
        geno2 = ""
        if len(patata) > 1:
            if patata[0] == patata[1]:
                geno = "HOM"
            else:
                geno = "HET"

            geno2 = alelos[int(patata[0])] + "/" + alelos[int(patata[1])]

        fichero_out.write("\t".join(linea[0:5]) + "\t" + geno + "\t" + geno2 + "\n")
