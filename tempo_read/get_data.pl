use strict;
use warnings;
use Term::ReadKey;

my $urs = "urs.earthdata.nasa.gov";
my $home_dir = $^O eq 'MSWin32' ? $ENV{"USERPROFILE"} : $ENV{"HOME"};
my $netrc_file = "$home_dir/.netrc";
$| = 1;

# Ask for username
print "Please enter your Earthdata Login username: ";
chomp(my $uid = <STDIN>);

# Ask for password (hidden input)
print "Please enter your Earthdata Login password: ";
ReadMode('noecho');
chomp(my $passwd = ReadLine(0));
ReadMode('restore');
print "\n";

# Escape '#' and '\'
$passwd =~ s/\\/\\\\/g;
$passwd =~ s/^#/\\#/;

# Build new .netrc content
my @netrc = ("machine $urs login $uid password $passwd");

# If existing .netrc exists, keep everything except old URS entry
if ( -e $netrc_file ) {
    open my $fh1, '<', $netrc_file or die "Could not open existing .netrc for reading\n";
    chomp(my @lines = <$fh1>);
    close $fh1;

    foreach (@lines) {
        unless (/^\s*machine\s+$urs\s+/) {
            push @netrc, $_;
        }
    }
}

# Write temporary file
open my $fh2, '>', "$netrc_file.tmp" or die "Could not create temp .netrc\n";
foreach (@netrc) { print $fh2 "$_\n"; }
close $fh2;

# Backup existing .netrc
if ( -e $netrc_file ) {
    unlink "$netrc_file.old" if -e "$netrc_file.old";
    rename $netrc_file, "$netrc_file.old";
}

# Replace with new file
rename "$netrc_file.tmp", $netrc_file
    or die "Could not move new .netrc into place\n";

print "Your .netrc file has been created/updated successfully.\n";
exit(0);
