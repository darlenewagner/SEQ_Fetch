#!/usr/bin/perl -w
use strict;
use LWP::Simple;
use XML::Simple;
use Data::Dumper;
use Cwd;

# Input:        First string for SAMN number of record and second string (optional) of output file path
# Requirements: i. LWP::Perl and NCBI command 'fetch.cgi' for retreival from NCBI across web
#               ii. XML::Simple to parse XML records downloaded from NCBI
#               iii. NCBI utility "sratoolkit" to be locally installed
# Output:       A sequence read archive (SRA) and extracted fastq file or files

## Installation: After installing sratoolkit, save or copy the script, 'fetch_SRA_fastq_using_SAMN.pl',
##               into the folder containing all sratoolkit programs (example: sratoolkit.2.4.2-ubuntu64/).
##               Alteratively, make a softlink from inside the sratoolkit folder,
##               For example, in folder sratoolkit.2.4.2-ubuntu64/, type command:
##               ln -s ../Documents/fetch_SRA_fastq_using_SAMN.pl fetch_SRA_file.pl, then chmod +x fetch_SRA_file.pl
##               assuming the script is saved in Documents/ and you want to name it 'fetch_SRA_file.pl'
##               To run in sratoolkit folder: ./fetch_SRA_file SAMN#

### Get command-line input

 my $SAMN = $ARGV[0];

 my $Path = $ARGV[1];

 my $Argument_Count = $#ARGV + 1;


  if($Argument_Count < 1)
    {
	print "NCBI SAMN number required as first argument!\n";
        die "Usage: fetch_SRA_File_using_SAMN.pl SAMN# Output_Folder (optional).\n$!";
    }


 ### Get NCBI database URLs 

 my $fetch = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=biosample&id=';

 my $url = $fetch.$SAMN;

 my $Xbiosample = get $url;

 ### Create XML::Simple object for data parsing

 my $xml1 = new XML::Simple (KeyAttr=>[]);

 my $biosamp_XML = $xml1->XMLin($Xbiosample);

 #### Debugging print through Data::Dumper
 #### print Dumper($biosamp_XML);

 print "Strain ID:\t";
 print $biosamp_XML->{BioSample}{Ids}{Id}[0]{content},"\n";

 my $sra_search = $biosamp_XML->{BioSample}{Ids}{Id}[0]{content};

 my $sra_ID_find = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=sra&term='.$sra_search;
 
 my $ID_query = get $sra_ID_find;
 
 my $xml2 = new XML::Simple (KeyAttr=>[]);

 my $query_XML = $xml2->XMLin($ID_query);

 #### print Dumper($query_XML);
 
 print "SRA Page ID:\t";
 print $query_XML->{IdList}{Id}, "\n";

 my $sra_ID = $query_XML->{IdList}{Id};

 my $sra_metadata = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=sra&id='.$sra_ID; 

 my $SRA_Meta = get $sra_metadata;

 my $xml3 = new XML::Simple (KeyAttr=>[]);
 
 my $SRA_XML = $xml3->XMLin($SRA_Meta);
 

  #### print Dumper($SRA_XML); 
  
  print "Content ID:\t";
  print $SRA_XML->{EXPERIMENT_PACKAGE}{SUBMISSION}{IDENTIFIERS}{SUBMITTER_ID}{content}, "\n";
 
  my $searchID = $SRA_XML->{EXPERIMENT_PACKAGE}{RUN_SET}{RUN}{IDENTIFIERS}{PRIMARY_ID};

 print "Archive ID:\t", $searchID, "\n"; 

 # exit;

my $pwd = cwd();

print $pwd, "\n";

chdir("sratoolkit.2.4.2-ubuntu64");
    
system("bin/prefetch -f yes $searchID");


 if(-d "../".$Path)
  {
     system("bin/fastq-dump -I --split-files $searchID -O ../$Path/$sra_search");
  }
 else
  {
     system("bin/fastq-dump -I --split-files $searchID -O ../$sra_search");
     chdir "..";
     my $pwd2 = cwd();
     print "WARNING: Folder pathname does not exist or was not specified.\n";
     print "Fastq saved under ", $pwd2, "/", $sra_search, "/\n";
  }

