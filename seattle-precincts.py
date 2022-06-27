import pandas
import geopandas

from matplotlib import colors

election = pandas.read_csv(f"elections/202111.csv", index_col=0, header=[0, 1])

precincts = geopandas.read_file(f"votdst_area__historic_shp/votdst_area_2021.shp")
election = election["City of Seattle Council Position No. 9"]
a, b = election.columns
election["diff"] = election[a] - election[b]
joined = precincts.merge(election, left_on="NAME", right_index=True)
print(joined)

ax = joined.plot(column="diff", figsize=(9*10,16*10), norm=colors.CenteredNorm(), cmap="coolwarm")
ax.set_axis_off()
ax.set_frame_on(False)
ax.margins(0)
ax.get_figure().savefig("seattle-results.png", bbox_inches='tight')
