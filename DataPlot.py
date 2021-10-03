import rasterio
import rasterio.plot as rplot
import matplotlib.pyplot as pyplot


def show_histogram_plot(file_name, bins=50, histtype='stepfilled', lw=0.0, stacked=False, alpha=0.3, rgb=True,
                        title=None):
    file_path = file_name + '.tiff'
    if not title:
        title = file_name

    with rasterio.open(file_path) as src:
        if rgb:
            fig, (axrgb, axhist) = pyplot.subplots(1, 2, figsize=(14, 7))
            fig.suptitle(title)
            rplot.show(src, ax=axrgb, title='RGB', cmap='pink')
            rplot.show_hist(src, bins=bins, histtype=histtype, lw=lw, stacked=stacked, alpha=alpha, ax=axhist,
                            title='Histogram')
            axhist.legend()
        else:
            rplot.show_hist(src, bins=bins, histtype=histtype, lw=lw, stacked=stacked, alpha=alpha, title=title)
            # pyplot.legend([src.read(1), src.read(2), src.read(3)], ['R', 'G', 'B'])

        pyplot.show()


def show_rgb_from_tiff(file_name, cmap='greys'):
    file_path = file_name + '.tiff'
    fig = pyplot.figure()
    with rasterio.open(file_path) as src:
        rplot.show(src, cmap=cmap)
