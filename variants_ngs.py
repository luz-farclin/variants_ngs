#!/usr/bin/env python
# -*- coding: utf-8 -*-

# The following program analyses the data generated by the NGS platforms
# You will have to enter on screen the necessary commands to
# tell the script what kind of data it is and what you want to do with it.

import os
import argparse


def argumentos():
    """
    Function that receives the arguments entered by the user and checks
    that are the basic arguments for carrying out the analysis.
    :return: object with arguments (args).
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='<string> [input directory]')
    parser.add_argument('-f', '--reference', help='<filename> [reference genome, fasta format]')
    parser.add_argument('-p', '--threads', help='<int> [default: 10]', default=10, type=int)
    parser.add_argument('-t', '--type', help='<string> [single or paired, default:paired]', default='paired', choices=['single', 'paired'])
    parser.add_argument('-q', '--quality', help='<int> [default: 20]', default=20, type=int)
    parser.add_argument('-o', '--output', help='<string> [output directory]', required=True)
    parser.add_argument('-b', '--bam', help='<string> [input directory containing BAM files]')
    parser.add_argument('-a', '--amplicon', help='<string> [amplicon or no_amplicon]', required=True, choices=['amplicon', 'no_amplicon'])
    args = parser.parse_args()

    if args.bam == None and args.input == None:
        print('-i, --input argument is mandatory')
        quit()
    return args


def crear_directorios(output):
    """
    Function that generates the directories where the
    results of the analysis.
    :param output: name of directory
    """

    os.system('mkdir -p ' + output + '/fastqc')
    os.system('mkdir -p ' + output + '/trimmed')
    os.system('mkdir -p ' + output + '/bwa')
    os.system('mkdir -p ' + output + '/annotate')
    os.system('mkdir -p ' + output + '/pileup')
    os.system('mkdir -p ' + output + '/vcf')


def obtener_nombre_ficheros(input, extension):
    """
    Function that receives a directory and the extension of the files to be searched
    in the directory, and returns a listing of the files in the
    that have that extension. Note: don't search in subdirectories.
    :param input: name of job directory
    :param extension: extension to search
    :return: list of files names
    """

    lista_ficheros = []
    for fichero in os.listdir(input):
        if (fichero.split(".")[-1]).lower() == extension.lower():
            lista_ficheros.append(fichero)
    return sorted(lista_ficheros)


def calidad_fichero(lista_ficheros, input, output):
    """
    Function that receives a FASTQ file and returns the quality of a FASTQC file
    with the quality of the sample.
    :param lista_ficheros: listing the files in the directory that have
    that extension
    :param input: name of the directory where you are going to work
    :param output: name of the output file
    :return: the results are dumped into the created directory
    """
    for fichero in lista_ficheros:
        os.system('fastqc {0}/{1} -o {2}/fastqc/'.format(input,fichero,output))


def trimming(lista_ficheros, input, output, type):
    """
    Function that performs the cleaning of the adapters of the sequences
    generated by NGS platforms.
    :param lista_ficheros: listing the files in the directory that have
    that extension
    :param input: name of the directory where you are going to work
    :param output: output file name
    :return:
    """

    if type == 'single':
        for fichero in lista_ficheros:
            os.system('cutadapt -q 20 -o {0}/trimmed/{1} {2}/{1}'.format(output,fichero,input))
    else:
        for i in range(0, len(lista_ficheros), 2):
            os.system('cutadapt -q 20 -o tmp.1.fastq -p tmp.2.fastq {0}/{1} {0}/{2}'.format(input, lista_ficheros[i],  lista_ficheros[i + 1]))
            os.system('cutadapt -q 20 -o {0}/trimmed/{1} -p {0}/trimmed/{2} tmp.2.fastq tmp.1.fastq'.format(output, lista_ficheros[i], lista_ficheros[i + 1]))
            os.system('rm tmp.1.fastq tmp.2.fastq')


def alineamiento(reference, input, output, type, extension, amplicon):
    """
    Function that receives the sequence that we want to analyze, the file
    reference and returns an aligned file that is saved in the
    corresponding.
    :param reference: reference sequence path
    :param output: output file name
    """

    # We made a list of the names of the files contained in the
    # folder we're going to work with
    lista_ficheros_trimmed = obtener_nombre_ficheros(output + '/trimmed/', extension) 

    # For each file we will trigger the alignment with the reference file
    if type == 'single':
        for fichero in lista_ficheros_trimmed:
            fichero_out = os.path.splitext(fichero)[0] + ".sam"
            os.system('bwa mem -t 10 {0} {1}/trimmed/{2} > {1}/bwa/{3}'.format(reference, output, fichero, fichero_out))
    else:
        for i in range(0, len(lista_ficheros_trimmed), 2):
            ficheroA = lista_ficheros_trimmed[i]
            ficheroB = lista_ficheros_trimmed[i + 1]
            fichero_out = os.path.splitext(ficheroA)[0] + ".sam"
            os.system('bwa mem -t 10 {0} {1}/trimmed/{2} {1}/trimmed/{3} > {1}/bwa/{4}'.format(reference, output, ficheroA, ficheroB, fichero_out))

    # For each .sam file generated
    lista = obtener_nombre_ficheros(output + '/bwa/', 'sam')
    for fichero in lista:
        fichero_out_bam = os.path.splitext(fichero)[0] + ".bam"
        os.system('samtools view -bS {0}/bwa/{1} > {0}/bwa/{2}'.format(output,fichero,fichero_out_bam))

    # We remove duplicates in the case of amplicons
    if amplicon == 'no_amplicon':
        lista2 = obtener_nombre_ficheros(output + '/bwa/', 'bam')
        for fichero in lista2:
            fichero_out_dup = os.path.splitext(fichero)[0] + "_dup.bam"
            os.system('samtools rmdup {0}/bwa/{1} {0}/bwa/{2}'.format(output, fichero, fichero_out_dup))
            os.system('mv {0}/bwa/{1} {0}/bwa/{2}'.format(output, fichero_out_dup, fichero))
    else:
        pass

    # We ordered the readings
    lista3 = obtener_nombre_ficheros(output + '/bwa/', 'bam')
    for fichero in lista3:
        fichero_out_sorted = os.path.splitext(fichero)[0] + "_sorted.bam"
        os.system('samtools sort {0}/bwa/{1} -o {0}/bwa/{2}'.format(output, fichero, fichero_out_sorted))


def variant_calling(reference, input, output):
    """
    Function that generates the VCF files
    :param reference: reference sequence path
    :param output: output file name
    """

    archivos_sorted = obtener_nombre_ficheros(output + '/bwa/', 'bam')
    for fichero in archivos_sorted:
        if fichero.count('_sorted') == 1:
            os.system('samtools mpileup -B -uf {0} {1}/bwa/{2} | bcftools call -mv -Ov | bcftools view -i "DP>=15" > {1}/pileup/{3}.vcf'.format(reference, output, fichero, os.path.splitext(fichero)[0]))

def anotation(output):
    """
    Function that performs the annotation of .vcf files    
    :param  output: output file name
    """

    vcfs = obtener_nombre_ficheros(output + '/pileup/', 'vcf')
    for fichero in vcfs:
        os.system("awk '{{print $1, $2, $4, $5, $10}}' {0}/pileup/{1} > {0}/annotate/{1}".format(output, fichero))
        os.system("sed -i 's/chr//g' {0}/annotate/{1}".format(output, fichero))
        os.system("awk '{{print $1{2}$2{2}$2{2}$3{2}$4{2}$5}}' {0}/annotate/{1} > {0}/annotate/{1}_awk.vcf".format(output, fichero,'"\\t"'))
        os.system("grep -v '#' {0}/annotate/{1}_awk.vcf > {0}/annotate/{1}_grep.vcf".format(output,fichero))
        os.system("python genotipo.py -i {0}/annotate/{1}_grep.vcf -o {0}/annotate/{1}".format(output,fichero))
        os.system("rm {0}/annotate/{1}_awk.vcf".format(output,fichero))
        os.system("rm {0}/annotate/{1}_grep.vcf".format(output,fichero))
        os.system("perl annovar/table_annovar.pl {0}/annotate/{1} annovar/humandb/ -buildver hg19 -out {0}/annotate/{1} -remove -protocol refGene,cytoBand,gnomad_exome,clinvar_20131105,exac03,avsnp147,dbnsfp30a -operation g,r,f,f,f,f,f -nastring . -csvout -polish -xref annovar/example/gene_fullxref.txt".format(output,fichero))
        os.system("awk -f filtro_awk {0}/annotate/{1}.{2}_multianno.csv > {0}/annotate/{1}.{2}_multianno_filtrado.csv".format(output,fichero,"hg19")
        os.system("python multianno_vcf_annot.py -i {0}/annotate/{1}.{2}_multianno_filtrado.csv -o {0}/annotate/{1}.{2}_multianno_filtrado_genot.csv -v {0}/annotate/{1}".format(output,fichero,"hg19"))
            
def main():
    """
    Funcion que ejecuta el programa.
    """

    ext = "fastq"
    argum = argumentos()
    crear_directorios(argum.output)
    ficheros = obtener_nombre_ficheros(argum.input, ext)
    calidad_fichero(ficheros, argum.input, argum.output)
    trimming(ficheros, argum.input, argum.output, argum.type)
    alineamiento(argum.reference, argum.input, argum.output, argum.type, ext, argum.amplicon)
    variant_calling(argum.reference, argum.input, argum.output)
    anotation(argm.output)


if __name__ == "__main__":
    main()