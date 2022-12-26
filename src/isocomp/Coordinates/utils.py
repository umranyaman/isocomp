"""Stand alone functions for dealing with genomic coordinates in isocomp"""
# pylint:disable=W0108
# std lib import
import logging
import os
# ext dependencies
import pyranges as pr

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = ['create_comparison_windows']


def update_source(gtf_pr: pr.PyRanges, new_source: str) -> pr.PyRanges:
    """Update the value in the source column of a pyranges obj read in 
    from a gtf/gff

    Args:
        gtf_pr (pr.PyRanges): a py.PyRanges object read in from a gff/gtf
        new_source (str): the value to enter into the Source column

    Returns:
        pr.PyRanges: the input pyranges obj with the updated Source column
    """
    if 'Source' not in gtf_pr.columns:
        raise KeyError(f'Column "Source" does not exist in '
                       f'{new_source+".gtf/gff"}')

    # update the value in the Source column
    gtf_pr.Source = new_source

    return gtf_pr


def create_comparison_windows(gtf_list: list, **kwargs) -> pr.PyRanges:
    """Read in gtf files to pyrange objects. To each gtf, replace the 'source' 
    with the base filename (no extention) of the gtf file. Filter on Feature 
    'transcript' and cluster overlapping ranges. Each cluster will be 
    sequentially numbered, so cluster 1 will comprise a discrete group of 
    transcripts with overlapping ranges, as will cluster 2, 3, ...

    Args:
        gtf_list (list): a list of paths to gtf files
        **kwargs (dict): optional keyword arguments for pr.merge()

    Raises:
        IOError: raised when gtf_list is not a list
        FileNotFoundError: raised when items in gtf_list are not found
        AssertionError: raised when the ext of gtf_list items is not .gtf 

    Returns:
        pr.PyRanges: A pyranges object with the columns Chromosome, Source 
        (source is replaced with the filename of the gtf file, which must be 
        unique in the set) Feature, Start, End, Score, Strand, Frame, 
        transcript_id, gene_id, Cluster
    """
    # check input
    logging.debug(gtf_list)
    if not isinstance(gtf_list, list):
        raise IOError('pyranges_list must be type list')
    for path in gtf_list:
        if not os.path.exists(path):
            raise FileNotFoundError(f'{path} does not exist')
        elif os.path.splitext(path)[1] != '.gtf':
            raise AssertionError(f'File extension of {path} is not gtf. This '
                                 f'must be a gtf file, and the way it is '
                                 f'confirmed is by the extension. '
                                 f'Either reformat to gtf or rename.')

    # read in data
    pyranges_list = [update_source(pr.read_gtf(x),
                                   os.path.splitext(os.path.basename(x))[0])
                     for x in gtf_list]

    # concat gtfs
    concat_ranges = pr.concat(pyranges_list)

    # merge ranges. pass any additional keyword arguments
    # from the function call to pr.merge
    # TODO address hardcoding of 'transcript' -- see
    # __validate_input() in __main__ for note on creating a config json
    concat_ranges = concat_ranges[concat_ranges.Feature == 'transcript']
    clustered_ranges = concat_ranges.cluster(**kwargs)

    logging.debug('number of merged ranges: %s',
                  str(max(clustered_ranges.Cluster)))

    return clustered_ranges
