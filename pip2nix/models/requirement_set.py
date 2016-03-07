from pip.req import RequirementSet


class RequirementSetLayer(RequirementSet):
    def __init__(self, *args, **kwargs):
        self.base_requirement_set = kwargs.pop('base')
        kwargs.setdefault('build_dir', self.base_requirement_set.build_dir)
        kwargs.setdefault('src_dir', self.base_requirement_set.src_dir)
        kwargs.setdefault('download_dir', self.base_requirement_set.download_dir)
        kwargs.setdefault('upgrade', self.base_requirement_set.upgrade)
        kwargs.setdefault('as_egg', self.base_requirement_set.as_egg)
        kwargs.setdefault('ignore_installed', self.base_requirement_set.ignore_installed)
        kwargs.setdefault('ignore_dependencies', self.base_requirement_set.ignore_dependencies)
        kwargs.setdefault('force_reinstall', self.base_requirement_set.force_reinstall)
        kwargs.setdefault('use_user_site', self.base_requirement_set.use_user_site)
        kwargs.setdefault('target_dir', self.base_requirement_set.target_dir)
        kwargs.setdefault('session', self.base_requirement_set.session)
        kwargs.setdefault('pycompile', self.base_requirement_set.pycompile)
        kwargs.setdefault('isolated', self.base_requirement_set.isolated)
        kwargs.setdefault('wheel_cache', self.base_requirement_set._wheel_cache)
        super(RequirementSetLayer, self).__init__(*args, **kwargs)

    def _prepare_file(
            self, finder, req_to_install, require_hashes=False,
            ignore_dependencies=False):
        if self.base_requirement_set.has_requirement(req_to_install.name):
            base_req = self.base_requirement_set.requirements[req_to_install.name]
            base_pkg_info = base_req.pkg_info()
            if not req_to_install.specifier.contains(base_pkg_info['Version']):
                # TODO: exceptions
                raise AssertionError(
                    ('There is already {req_name}=={base_pkg_version} downloaded, '
                     'but {comes_from} requires {req_name}{req_spec}')
                    .format(
                        req_name=req_to_install.name,
                        req_spec=req_to_install.specifier,
                        base_pkg_version=base_pkg_info['Version'],
                        comes_from=req_to_install.comes_from.name))
            return []
        else:
            extras = super(RequirementSetLayer, self) \
                ._prepare_file(
                    finder, req_to_install, require_hashes=require_hashes,
                    ignore_dependencies=ignore_dependencies)
            return extras
