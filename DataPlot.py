from os import remove
from numpy import linspace, arange, nan
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


def show_rgb_from_tiff(file_name, cmap='pink'):
    file_path = file_name + '.tiff'
    fig = pyplot.figure()
    with rasterio.open(file_path) as src:
        rplot.show(src, cmap=cmap)


def compare_tiff_files(file_list: list(), titles=None, cmap='pink'):
    n_files = len(file_list)
    if n_files <= 3:
        n_cols = n_files
        n_rows = 1
    else:
        n_cols = 3
        n_rows = int(n_files / n_cols + 1)

    fig, axs = pyplot.subplots(n_rows, n_cols)

    i_row, i_col = 1, 1
    for i_plot in range(len(file_list)):
        ax_plt_obj = pyplot.subplot(int(''.join([str(arg) for arg in [n_rows, n_cols, i_plot+1]])))
        if titles:
            title = titles[i_plot]
        else:
            title = file_list[i_plot].split('/')[-1]

        try:
            with rasterio.open(file_list[i_plot].rstrip('.tif')+'.tiff') as src:
                rplot.show(src, ax=ax_plt_obj, transform=src.transform, cmap=cmap, title=title)
        except rasterio.errors.RasterioIOError:
            try:
                with rasterio.open(file_list[i_plot].rstrip('.tif')+'.tif') as src:
                    rplot.show(src, ax=ax_plt_obj, transform=src.transform, cmap=cmap, title=title)
            except rasterio.errors.RasterioIOError as err:
                raise err


        i_col += 1
        if i_plot == n_cols:
            i_row += 1
            i_col = 0

    pyplot.show()


def plot_data_array(array_2D, crs:str, transform, dtype, save=False, show=True):
    pyplot.imshow(array_2D)
    height, width = array_2D.shape
    if save:
        with rasterio.open(save, 'w', driver='Gtiff',
                           width=width, height=height, dtype=dtype,
                           count=1, crs=crs, transform=transform) as tiff_img:
            tiff_img.write(array_2D, 1)

        print(f"Picture saved: {save}")


def true_color_img(r_band, g_band, b_band, crs:str, transform, dtype, show=True, save=False, cmap='pink'):

    if save:
        file_name = save
    else:
        file_name = 'temp_true_colour.tiff'

    height, width = r_band.shape

    with rasterio.open(file_name, 'w', driver='Gtiff',
                       width=width, height=height, dtype=dtype,
                       count=3, crs=crs, transform=transform) as true_color_img:
        true_color_img.write(r_band, 1)  # red
        true_color_img.write(g_band, 2)  # green
        true_color_img.write(b_band, 3)  # blue

    if show:
        with rasterio.open(file_name) as src:
            rplot.show(src, transform=transform, cmap=cmap)

    if not save:
        remove(file_name)


def plot_pegel(pegel_list, measure, save=False, station_name=None, title=None):
    # find x tick subset

    if measure == 'waterlevel':
        value_name = pegel_list[0].waterlevel.columns[-1]
        time_stamps = pegel_list[0].waterlevel['timestamp']
    elif measure == 'discharge':
        value_name = pegel_list[0].discharge.columns[-1]
        time_stamps = pegel_list[0].discharge['timestamp']
    else:
        print("Plot couldn't be created. Choose one of the allowed measures [waterlevel, discharge]")
        exit()

    if len(time_stamps) > 10:
        for i in range(len(time_stamps)):
            xticks = [time_stamps.iloc[i*int(len(time_stamps)/10)] for i in range(10)]
            xtick_loc = [i*int(len(time_stamps)/10) for i in range(10)]
    else:
        xticks = list(time_stamps)
        xtick_loc = [i for i in range(len(time_stamps))]

    min_value, max_value = 500, 0

    fig = pyplot.figure()
    fig.suptitle(f"Pegel from {time_stamps.iloc[0][:-9]} to {time_stamps.iloc[len(time_stamps)-1][:-9]}")
    for i in range(len(pegel_list)):
        if measure == 'waterlevel':
            data_values = list(map(int, pegel_list[i].waterlevel[value_name]))
        elif measure == 'discharge':
            data_values = list(map(float, pegel_list[i].discharge[value_name]))
        # filter for nan values
        for j in range(len(data_values)):
            if data_values[j] == -777:
                data_values[j] = nan

        pyplot.plot(time_stamps, data_values, label=pegel_list[i].station_name)

        # data_values = list(filter((-777).__ne__, data_values))
        if min(data_values) < min_value:
            min_value = min(data_values)
        if max(data_values) > max_value:
            max_value = max(data_values)

    pyplot.xticks(xtick_loc, xticks, rotation=75)
    # pyplot.yticks(ytick_loc, y_ticks)
    pyplot.xlabel('time')
    pyplot.ylabel(value_name)
    pyplot.legend()
    pyplot.tight_layout()
    pyplot.show()

    if save:
        file_name = save
        pyplot.savefig(file_name.rstrip('.png') + '.png')