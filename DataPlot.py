from os import remove

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


def plot_data_array(array_2D, x_min=None, x_max=None, y_min=None, y_max=None, cmap='pink'):
    pyplot.imshow(array_2D)
    pyplot.show()


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


def plot_pegel(pegel, save=False, station_name=None, title=None):
    # find x tick subset
    time_stamps = pegel['timestamp']
    pegel_values = pegel['Wasserstand [m ü.NN]']

    if len(time_stamps) > 15:
        for i in range(len(time_stamps)):
            day = time_stamps[i][0:10]
            hour = time_stamps[i][-14:-9]

            if not 'days' in locals():
                days = [(day, i)]
                hours = [(hour, i)]
            elif day != days[-1][0]:
                days.append((day, i))

            if hour != hours[-1][0] and hour[-2:] == '00':
                hours.append((hour, i))

    if len(days) > 1:
        xticks = [day[0] for day in days[:]]
        xtick_loc = [day[1] for day in days[:]]
    else:
        xticks = [hour[0] for hour in hours[:]]
        xtick_loc = [hour[1] for hour in hours[:]]
    fig = pyplot.figure()
    if station_name:
        fig.suptitle(f"Pegel: {station_name} from {time_stamps[0][:-9]} to {time_stamps[-1][:-9]}")
    pyplot.plot(time_stamps, pegel_values, 'rs')
    pyplot.xticks(xtick_loc, xticks, rotation=90)
    pyplot.xlabel(pegel.columns[0])
    pyplot.ylabel(pegel.columns[1])

    pyplot.tight_layout()
    pyplot.show()

    if save:
        file_name = save
        pyplot.savefig(file_name.rstrip('.png') + '.png')